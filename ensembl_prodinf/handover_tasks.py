'''
Tasks and entrypoint need to accept and sequentially process a database. 
The data flow is:
1. handover_database (standard function)
- checks existence of database
- submits HCs if appropriate and submits celery task process_checked_db
- if not, submits copy and submits celery task process_copied_db
2. process_checked_db (celery task)
- wait/retry until healthcheck job has completed
- if success, submit copy job and submits celery task process_copied_db
3. process_copied_db (celery task)
- wait/retry until copy job has completed
- if success, submit metadata update job and submit celery task process_db_metadata
4. process_db_metadata (celery task)
- wait/retry until metadara load job has completed
- if success, process event using a event handler endpoint celery task
@author: dstaines
'''
from ensembl_prodinf.handover_celery_app import app

from hc_client import HcClient
from db_copy_client import DbCopyClient
from metadata_client import MetadataClient
from event_client import EventClient
from sqlalchemy_utils.functions import database_exists
from sqlalchemy.engine.url import make_url
from .utils import send_email
import handover_config as cfg
import uuid     
import re
import reporting

pool = reporting.get_pool(cfg.report_server)
hc_client = HcClient(cfg.hc_uri)
db_copy_client = DbCopyClient(cfg.copy_uri)
metadata_client = MetadataClient(cfg.meta_uri)
event_client = EventClient(cfg.event_uri)
     
def get_logger():    
    return reporting.get_logger(pool, cfg.report_exchange, 'handover', None, {})
                
def handover_database(spec):    
    """ Method to accept a new database for incorporation into the system 
    Argument is a dict with the following keys:
    * src_uri - URI to database to handover (required) 
    * tgt_uri - URI to copy database to (optional - generated from staging and src_uri if not set)
    * contact - email address of submitter (required)
    * type - string describing type of update (required)
    * comment - additional information about submission (required)
    The following keys are added during the handover process:
    * handover_token - unique identifier for this particular handover invocation
    * hc_job_id - job ID for healthcheck process
    * db_job_id - job ID for database copy process
    * metadata_job_id - job ID for the metadata loading process
    * progress_total - Total number of task to do
    * progress_complete - Total number of task completed
    """
    # TODO verify dict    
    reporting.set_logger_context(get_logger(), spec['src_uri'], spec)    
    # create unique identifier
    spec['handover_token'] = str(uuid.uuid1())
    if 'tgt_uri' not in spec:
        spec['tgt_uri'] = get_tgt_uri(spec['src_uri'])
    get_logger().info("Handling " + str(spec))
    check_db(spec['src_uri'])
    groups = groups_for_uri(spec['src_uri'])
    spec['progress_total']=3
    spec['progress_complete']=1
    submit_hc(spec, groups)
    return spec['handover_token']

def get_tgt_uri(src_uri):
    """Create target URI from staging details and name of source database"""
    url = make_url(src_uri)
    return str(cfg.staging_uri) + str(url.database)

    
def check_db(uri):    
    """Check if source database exists"""
    if(database_exists(uri) == False):
        get_logger().error(uri + " does not exist")
        raise ValueError(uri + " does not exist")
    else:
        return

core_pattern = re.compile(".*[a-z]_(core|rnaseq|cdna|otherfeatures)_[0-9].*")   
variation_pattern = re.compile(".*[a-z]_variation_[0-9].*")   
compara_pattern = re.compile(".*[a-z]_compara_[0-9].*")   
funcgen_pattern = re.compile(".*[a-z]_funcgen_[0-9].*")
def groups_for_uri(uri):
    """Find which HC group to run on a given database"""
    if(core_pattern.match(uri)):
        return [cfg.core_handover_group]
    elif(variation_pattern.match(uri)):
        return [cfg.variation_handover_group]
    elif(funcgen_pattern.match(uri)):
        return [cfg.funcgen_handover_group]
    elif(compara_pattern.match(uri)):
        return [cfg.compara_handover_group]
    else:
        return None


def submit_hc(spec, groups):
    """Submit the source database for healthchecking. Returns a celery job identifier"""
    hc_job_id = hc_client.submit_job(spec['src_uri'], cfg.production_uri, cfg.compara_uri, cfg.staging_uri, cfg.live_uri, None, groups, cfg.data_files_path, None, spec['handover_token'])
    spec['hc_job_id'] = hc_job_id
    task_id = process_checked_db.delay(hc_job_id, spec)
    get_logger().debug("Submitted DB for checking as " + str(task_id))
    if 'email_notification' in spec:
        send_email(to_address=spec['contact'], subject='HC submitted', body=str(spec['src_uri']) + ' has been submitted for checking. Please see '+cfg.hc_web_uri + str(hc_job_id), smtp_server=cfg.smtp_server)
    return task_id

@app.task(bind=True)
def process_checked_db(self, hc_job_id, spec):
    """ Task to wait until HCs finish and then respond e.g.
    * submit copy if HCs succeed
    * send error email if not
    """
    reporting.set_logger_context(get_logger(), spec['src_uri'], spec)    
    # allow infinite retries 
    self.max_retries = None
    get_logger().info("HCs in progress, please see: " +cfg.hc_web_uri + str(hc_job_id))
    result = hc_client.retrieve_job(hc_job_id)
    if (result['status'] == 'incomplete') or (result['status'] == 'running') or (result['status'] == 'submitted'):
        get_logger().debug("HC Job incomplete, checking again later")
        raise self.retry()
    
    # check results
    if (result['status'] == 'failed'):
        get_logger().info("HCs failed to run")    
        msg = """
Running healthchecks vs %s failed to execute.
Please see %s
""" % (spec['src_uri'], cfg.hc_web_uri + str(hc_job_id))
        if 'email_notification' in spec:
             send_email(to_address=spec['contact'], subject='HC failed to run', body=msg, smtp_server=cfg.smtp_server)
        return 
    elif (result['output']['status'] == 'failed'):
        get_logger().info("HCs found problems, please see: "+cfg.hc_web_uri + str(hc_job_id))
        msg = """
Running healthchecks vs %s completed but found failures.
Please see %s
""" % (spec['src_uri'], cfg.hc_web_uri + str(hc_job_id))
        if 'email_notification' in spec:
            send_email(to_address=spec['contact'], subject='HC ran but failed', body=msg, smtp_server=cfg.smtp_server)
        return
    else:
        if 'email_notification' in spec:
            send_email(to_address=spec['contact'], subject='HC fine', body=str(spec['src_uri']) + ' has passed healthchecks ', smtp_server=cfg.smtp_server)
        get_logger().info("HCs fine, starting copy")
        spec['progress_complete']=2
        submit_copy(spec)


def submit_copy(spec):
    """Submit the source database for copying to the target. Returns a celery job identifier"""    
    copy_job_id = db_copy_client.submit_job(spec['src_uri'], spec['tgt_uri'], None, None, False, True, None)
    spec['copy_job_id'] = copy_job_id
    task_id = process_copied_db.delay(copy_job_id, spec)    
    get_logger().debug("Submitted DB for copying as " + str(task_id))
    if 'email_notification' in spec:
        send_email(to_address=spec['contact'], subject='Database copy submitted', body=str('Database copy from ' + spec['src_uri']) + ' to ' + spec['tgt_uri'] + ' submitted. Please see '+ cfg.copy_web_uri + str(copy_job_id), smtp_server=cfg.smtp_server)
    return task_id


@app.task(bind=True)    
def process_copied_db(self, copy_job_id, spec):
    """Wait for copy to complete and then respond accordingly:
    * if success, submit to metadata database
    * if failure, flag error using email"""
    reporting.set_logger_context(get_logger(), spec['src_uri'], spec)    
    # allow infinite retries     
    self.max_retries = None
    get_logger().info("Copying in progress, please see: " +cfg.copy_web_uri + str(copy_job_id))
    result = db_copy_client.retrieve_job(copy_job_id)
    if (result['status'] == 'incomplete') or (result['status'] == 'running') or (result['status'] == 'submitted'):
        get_logger().debug("Database copy job incomplete, checking again later")
        raise self.retry()
    if (result['status'] == 'failed'):
        get_logger().info("Copy failed, please see: "+cfg.copy_web_uri + str(copy_job_id))
        msg = """
Copying %s to %s failed.
Please see %s
""" % (spec['src_uri'], spec['tgt_uri'], cfg.copy_web_uri + str(copy_job_id))
        if 'email_notification' in spec:
            send_email(to_address=spec['contact'], subject='Database copy failed', body=msg, smtp_server=cfg.smtp_server)
        return
    else:
        if 'email_notification' in spec:
            send_email(to_address=spec['contact'], subject='Database copy successful', body=str('Database copy from' + spec['src_uri']) + ' to ' + spec['tgt_uri'] + ' successful', smtp_server=cfg.smtp_server)
        get_logger().info("Copying complete, submitting metadata job")
        spec['progress_complete']=3
        submit_metadata_update(spec)
    

def submit_metadata_update(spec):
    """Submit the source database for copying to the target. Returns a celery job identifier."""
    metadata_job_id = metadata_client.submit_job( spec['tgt_uri'], None, None, None, None, spec['contact'], spec['type'], spec['comment'], 'Handover', None)
    spec['metadata_job_id'] = metadata_job_id
    task_id = process_db_metadata.delay(metadata_job_id, spec)
    get_logger().debug("Submitted DB for metadata loading " + str(task_id))
    if 'email_notification' in spec:
        send_email(to_address=spec['contact'], subject='Metadata load submitted', body=str(spec['tgt_uri']) + ' submitted for metadata load.' + ' Please see ' + cfg.meta_web_uri + str(metadata_job_id), smtp_server=cfg.smtp_server)
    return task_id


@app.task(bind=True)    
def process_db_metadata(self, metadata_job_id, spec):
    """Wait for metadata update to complete and then respond accordingly:
    * if success, submit event to event handler for further processing
    * if failure, flag error using email"""
    reporting.set_logger_context(get_logger(), spec['tgt_uri'], spec)
    # allow infinite retries
    self.max_retries = None
    get_logger().info("Loading into metadata database, please see: "+cfg.meta_uri + "jobs/"+ str(metadata_job_id))
    result = metadata_client.retrieve_job(metadata_job_id)
    if (result['status'] == 'incomplete') or (result['status'] == 'running') or (result['status'] == 'submitted'):
        get_logger().debug("Metadata load Job incomplete, checking again later")
        raise self.retry()
    if (result['status'] == 'failed'):
        get_logger().info("Metadata load failed, please see "+cfg.meta_uri+ 'jobs/' + str(metadata_job_id) + '?format=failures')
        msg = """
Metadata load of %s failed.
Please see %s
""" % (spec['tgt_uri'], cfg.meta_uri + str(metadata_job_id))
        if 'email_notification' in spec:
            send_email(to_address=spec['contact'], subject='Metadata load failed, please see: '+cfg.meta_uri+ 'jobs/' + str(metadata_job_id) + '?format=failures', body=msg, smtp_server=cfg.smtp_server)
        return
    else:
        #get_logger().info("Metadata load complete, submitting event")
        get_logger().info("Metadata load complete, Handover successful")
        if 'email_notification' in spec:
            send_email(to_address=spec['contact'], subject='Metadata load successful', body=str(spec['tgt_uri']) + ' successfully loaded into metadata database. Handover successful', smtp_server=cfg.smtp_server)
        #submit_event(spec,result)
    return

def submit_event(spec,result):
    """Submit an event"""
    print(result['output']['events'])
    for event in result['output']['events']:
        print(event)
        event_client.submit_job({"type":event['type'],"genome":event['genome']})
        get_logger().debug("Submitted event to event handler endpoint")