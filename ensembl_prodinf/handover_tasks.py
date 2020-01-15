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
from ensembl.datacheck.client import DatacheckClient
from sqlalchemy_utils.functions import database_exists, drop_database
from sqlalchemy.engine.url import make_url
from .utils import send_email
from .models.compara import check_grch37
from .models.core import get_division
import handover_config as cfg
import uuid
import re
import reporting
import json

pool = reporting.get_pool(cfg.report_server)
hc_client = HcClient(cfg.hc_uri)
db_copy_client = DbCopyClient(cfg.copy_uri)
metadata_client = MetadataClient(cfg.meta_uri)
event_client = EventClient(cfg.event_uri)
dc_client = DatacheckClient(cfg.dc_uri)

db_types_list = [i for i in cfg.allowed_database_types.split(",")]
species_pattern = re.compile(r'^(?P<prefix>\w+)_(?P<type>core|rnaseq|cdna|otherfeatures|variation|funcgen)(_\d+)?_(?P<release>\d+)_(?P<assembly>\d+)$')
compara_pattern = re.compile(r'^ensembl_compara(_(?P<division>[a-z]+|pan)(_homology)?)?(_(\d+))?(_\d+)$')
ancestral_pattern = re.compile(r'^ensembl_ancestral_\d+$')

def get_logger():
    return reporting.get_logger(pool, cfg.report_exchange, 'handover', None, {})

def handover_database(spec):
    """ Method to accept a new database for incorporation into the system
    Argument is a dict with the following keys:
    * src_uri - URI to database to handover (required)
    * tgt_uri - URI to copy database to (optional - generated from staging and src_uri if not set)
    * contact - email address of submitter (required)
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
    spec['progress_total']=3
    check_db(spec['src_uri'])
    src_url = make_url(spec['src_uri'])
    #Scan database name and retrieve species or compara name, database type, release number and assembly version
    (db_prefix, db_type, release, assembly) = parse_db_infos(src_url.database)
    # Check if the given database can be handed over
    if db_type not in db_types_list:
        get_logger().error("Handover failed, " + spec['src_uri'] + " has been handed over after deadline. Please contact the Production team")
        raise ValueError(spec['src_uri'] + " has been handed over after the deadline. Please contact the Production team")
    #Get database hc group and compara_uri
    (groups,compara_uri) = hc_groups(db_type,db_prefix,spec['src_uri'])
    #Check to which staging server the database need to be copied to
    (spec,staging_uri,live_uri) = check_staging_server(spec,db_type,db_prefix,assembly)
    #setting compara url to default value for species databases. This value is only used by Compara healthchecks
    if compara_uri is None:
        compara_uri=cfg.compara_uri + 'ensembl_compara_master'
    if 'tgt_uri' not in spec:
        spec['tgt_uri'] = get_tgt_uri(src_url,staging_uri)
    spec['staging_uri'] = staging_uri
    spec['progress_complete']=0
    get_logger().info("Handling " + str(spec))
    submit_dc(spec, src_url, db_type, db_prefix, release, staging_uri, compara_uri)
    submit_hc(spec, groups, compara_uri, staging_uri, live_uri)
    return spec['handover_token']

def get_tgt_uri(src_url,staging_uri):
    """Create target URI from staging details and name of source database"""
    return str(staging_uri) + str(src_url.database)


def check_db(uri):
    """Check if source database exists"""
    if not database_exists(uri):
        get_logger().error("Handover failed, " + uri + " does not exist")
        raise ValueError(uri + " does not exist")
    else:
        return

def parse_db_infos(database):
    """Parse database name and extract db_prefix and db_type. Also extract release and assembly for species databases"""
    if species_pattern.match(database):
        m = species_pattern.match(database)
        db_prefix = m.group('prefix')
        db_type = m.group('type')
        release = m.group('release')
        assembly = m.group('assembly')
        return db_prefix, db_type, release, assembly
    elif compara_pattern.match(database):
        m = compara_pattern.match(database)
        division = m.group('division')
        db_prefix = division if division else 'compara'
        return db_prefix, 'compara', None, None
    elif ancestral_pattern.match(database):
        return 'ensembl', 'ancestral', None, None
    else:
        raise ValueError("Database type for "+database+" is not expected. Please contact the Production team")

def hc_groups(db_type,db_prefix,uri):
    """Find which HC group to run on a given database type. For Compara generate the compara master uri"""
    if db_type in ['core','rnaseq','cdna','otherfeatures']:
        return [cfg.core_handover_group],None
    elif db_type == 'variation':
        return [cfg.variation_handover_group],None
    elif db_type == 'funcgen':
        return [cfg.funcgen_handover_group],None
    elif db_type == 'ancestral':
        return [cfg.ancestral_handover_group],None
    elif db_type == 'compara':
        if db_prefix == "pan":
            compara_uri=cfg.compara_uri + db_prefix + '_compara_master'
            compara_handover_group=cfg.compara_pan_handover_group
        elif db_prefix == "plants":
            compara_uri=cfg.compara_plants_uri + 'ensembl_compara_master_' + db_prefix
            compara_handover_group=cfg.compara_handover_group
        elif db_prefix == "metazoa":
            compara_uri=cfg.compara_metazoa_uri + 'ensembl_compara_master_' + db_prefix
            compara_handover_group=cfg.compara_handover_group
        elif check_grch37(uri,'homo_sapiens'):
            compara_uri=cfg.compara_grch37_uri + 'ensembl_compara_master_grch37'
            compara_handover_group=cfg.compara_handover_group
        elif db_prefix:
            compara_uri=cfg.compara_uri + db_prefix + '_compara_master'
            compara_handover_group=cfg.compara_handover_group
        else:
            compara_uri=cfg.compara_uri + 'ensembl_compara_master'
            compara_handover_group=cfg.compara_handover_group
        return [compara_handover_group],compara_uri

def check_staging_server(spec,db_type,db_prefix,assembly):
    """Find which staging server should be use. secondary_staging for GRCh37 and Bacteria, staging for the rest"""
    if 'bacteria' in db_prefix:
        staging_uri = cfg.secondary_staging_uri
        live_uri = cfg.secondary_live_uri
    elif db_prefix == 'homo_sapiens' and assembly == '37':
        staging_uri = cfg.secondary_staging_uri
        live_uri = cfg.secondary_live_uri
        spec['GRCh37']=1
        spec['progress_total']=2
    elif db_type == 'compara' and check_grch37(spec['src_uri'],'homo_sapiens'):
        staging_uri = cfg.secondary_staging_uri
        live_uri = cfg.secondary_live_uri
        spec['GRCh37']=1
        spec['progress_total']=2
    else:
        staging_uri = cfg.staging_uri
        live_uri = cfg.live_uri
    return spec,staging_uri,live_uri


def submit_hc(spec, groups, compara_uri, staging_uri, live_uri):
    """Submit the source database for healthchecking. Returns a celery job identifier"""
    try:
        hc_job_id = hc_client.submit_job(spec['src_uri'], cfg.production_uri, compara_uri, staging_uri, live_uri, None, groups, cfg.data_files_path, None, spec['handover_token'])
    except Exception as e:
        get_logger().error("Handover failed, Cannot submit hc job")
        raise ValueError("Handover failed, Cannot submit hc job {}".format(e))
    spec['hc_job_id'] = hc_job_id
    task_id = process_checked_db.delay(hc_job_id, spec)
    get_logger().debug("Submitted DB for checking as " + str(task_id))
    return task_id

def submit_dc(spec, src_url, db_type, db_prefix, release, staging_uri, compara_uri):
    """Submit the source database for healthchecking. Returns a celery job identifier"""
    try:
        server_url = 'mysql://'+str(src_url.username)+'@'+str(src_url.host)+':'+str(src_url.port)+"/"
        if db_type == 'compara':
            get_logger().debug("Submitting DC for "+src_url.database+ " on server: "+server_url)
            dc_job_id = dc_client.submit_job(server_url, src_url.database, None, None, None, release, None, db_type, 'critical', db_prefix, None, spec['handover_token'])
        elif db_type in ['rnaseq','cdna','otherfeatures']:
            get_logger().debug("Submitting DC for "+src_url.database+ " on server: "+server_url)
            dc_job_id = dc_client.submit_job(server_url, src_url.database, None, None, None, release, None, 'corelike', 'critical', db_prefix, None, spec['handover_token'])
        else:
            get_logger().debug("src_uri: "+spec['src_uri']+" dbtype "+db_type+" server_url "+server_url)
            division = get_division(spec['src_uri'],db_type)
            get_logger().debug("division: "+division)
            get_logger().debug("Submitting DC for "+src_url.database+ " on server: "+server_url)
            dc_job_id = dc_client.submit_job(server_url, src_url.database, None, None, None, release, None, db_type, 'critical', division, None, spec['handover_token'])
    except Exception as e:
        get_logger().debug("Cannot submit dc job {}".format(e))
        #get_logger().error("Handover failed, Cannot submit dc job")
        #raise ValueError("Handover failed, Cannot submit dc job {}".format(e))
    #spec['dc_job_id'] = dc_job_id
    #task_id = process_datachecked_db.delay(dc_job_id, spec)
    #get_logger().debug("Submitted DB for checking as " + str(task_id))
    #return task_id
    return

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
    try:
        result = hc_client.retrieve_job(hc_job_id)
    except Exception as e:
        get_logger().error("Handover failed, cannot retrieve hc job")
        raise ValueError("Handover failed, cannot retrieve hc job {}".format(e))
    if result['status'] in ['incomplete', 'running', 'submitted']:
        get_logger().debug("HC Job incomplete, checking again later")
        raise self.retry()
    # check results
    if result['status'] == 'failed':
        get_logger().info("HCs failed to run, please see: "+cfg.hc_web_uri + str(hc_job_id))
        msg = """
Running healthchecks on %s failed to execute.
Please see %s
""" % (spec['src_uri'], cfg.hc_web_uri + str(hc_job_id))
        send_email(to_address=spec['contact'], subject='HC failed to run', body=msg, smtp_server=cfg.smtp_server)
        return
    elif result['output']['status'] == 'failed':
        get_logger().info("HCs found problems, please see: "+cfg.hc_web_uri + str(hc_job_id))
        msg = """
Running healthchecks on %s completed but found failures.
Please see %s
""" % (spec['src_uri'], cfg.hc_web_uri + str(hc_job_id))
        send_email(to_address=spec['contact'], subject='HC ran but failed', body=msg, smtp_server=cfg.smtp_server)
        return
    else:
        get_logger().info("HCs fine, starting copy")
        spec['progress_complete']=1
        submit_copy(spec)

@app.task(bind=True)
def process_datachecked_db(self, dc_job_id, spec):
    """ Task to wait until DCs finish and then respond e.g.
    * submit copy if DC succeed
    * send error email if not
    """
    reporting.set_logger_context(get_logger(), spec['src_uri'], spec)
    # allow infinite retries
    self.max_retries = None
    get_logger().info("DC in progress, please see: " +cfg.dc_uri + "/datacheck/jobs/" + str(dc_job_id))
    try:
        result = dc_client.retrieve_job(dc_job_id)
    except Exception as e:
        get_logger().error("Handover failed, cannot retrieve dc job")
        raise ValueError("Handover failed, cannot retrieve dc job {}".format(e))
    if result['status'] in ['incomplete', 'running', 'submitted']:
        get_logger().debug("HC Job incomplete, checking again later")
        raise self.retry()
    # check results
    if result['status'] == 'failed':
        get_logger().info("DCs failed to run, please see: "+cfg.dc_uri + "/datacheck/jobs/" + str(dc_job_id))
        msg = """
Running datachecks on %s failed to execute.
Please see %s
""" % (spec['src_uri'], cfg.dc_uri + "/datacheck/jobs/" + str(dc_job_id))
        send_email(to_address=spec['contact'], subject='DC failed to run', body=msg, smtp_server=cfg.smtp_server)
        return
    elif result['output']['failed_total'] > 0:
        get_logger().info("DCs found problems, please see: "+cfg.dc_uri + "/datacheck/jobs/" + str(dc_job_id))
        msg = """
Running datachecks on %s completed but found failures.
Please see %s
""" % (spec['src_uri'], cfg.dc_uri + "/datacheck/jobs/" + str(dc_job_id))
        send_email(to_address=spec['contact'], subject='DC ran but failed', body=msg, smtp_server=cfg.smtp_server)
        return
    else:
        get_logger().info("DCs fine, starting copy")
        spec['progress_complete']=1
        submit_copy(spec)

def submit_copy(spec):
    """Submit the source database for copying to the target. Returns a celery job identifier"""
    try:
        copy_job_id = db_copy_client.submit_job(spec['src_uri'], spec['tgt_uri'], None, None, False, True, True, None, None)
    except Exception as e:
        get_logger().error("Handover failed, cannot submit copy job")
        raise ValueError("Handover failed, cannot submit copy job {}".format(e))
    spec['copy_job_id'] = copy_job_id
    task_id = process_copied_db.delay(copy_job_id, spec)
    get_logger().debug("Submitted DB for copying as " + str(task_id))
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
    try:
        result = db_copy_client.retrieve_job(copy_job_id)
    except Exception as e:
        get_logger().error("Handover failed, cannot retrieve copy job")
        raise ValueError("Handover failed, cannot retrieve copy job {}".format(e))
    if result['status'] in ['incomplete', 'running', 'submitted']:
        get_logger().debug("Database copy job incomplete, checking again later")
        raise self.retry()
    if result['status'] == 'failed':
        get_logger().info("Copy failed, please see: "+cfg.copy_web_uri + str(copy_job_id))
        msg = """
Copying %s to %s failed.
Please see %s
""" % (spec['src_uri'], spec['tgt_uri'], cfg.copy_web_uri + str(copy_job_id))
        send_email(to_address=spec['contact'], subject='Database copy failed', body=msg, smtp_server=cfg.smtp_server)
        return
    elif 'GRCh37'in spec:
        get_logger().info("Copying complete, Handover successful")
        spec['progress_complete']=2
    else:
        get_logger().info("Copying complete, submitting metadata job")
        spec['progress_complete']=2
        submit_metadata_update(spec)

def submit_metadata_update(spec):
    """Submit the source database for copying to the target. Returns a celery job identifier."""
    try:
        metadata_job_id = metadata_client.submit_job( spec['tgt_uri'], None, None, None, None, spec['contact'], spec['comment'], 'Handover', None)
    except Exception as e:
        get_logger().error("Handover failed, cannot submit metadata job")
        raise ValueError("Handover failed, cannot submit metadata job {}".format(e))
    spec['metadata_job_id'] = metadata_job_id
    task_id = process_db_metadata.delay(metadata_job_id, spec)
    get_logger().debug("Submitted DB for metadata loading " + str(task_id))
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
    try:
        result = metadata_client.retrieve_job(metadata_job_id)
    except Exception as e:
        get_logger().error("Handover failed, Cannot retrieve metadata job")
        raise ValueError("Handover failed, Cannot retrieve metadata job {}".format(e))
    if result['status'] in ['incomplete', 'running', 'submitted']:
        get_logger().debug("Metadata load Job incomplete, checking again later")
        raise self.retry()
    if result['status'] == 'failed':
        get_logger().info("Metadata load failed, please see "+cfg.meta_uri+ 'jobs/' + str(metadata_job_id) + '?format=failures')
        msg = """
Metadata load of %s failed.
Please see %s
""" % (spec['tgt_uri'], cfg.meta_uri+ 'jobs/' + str(metadata_job_id) + '?format=failures')
        send_email(to_address=spec['contact'], subject='Metadata load failed, please see: '+cfg.meta_uri+ 'jobs/' + str(metadata_job_id) + '?format=failures', body=msg, smtp_server=cfg.smtp_server)
        return
    else:
        #Cleaning up old assembly or old genebuild databases for Wormbase when database suffix has changed
        if 'events' in result['output'] and result['output']['events']:
            for event in result['output']['events']:
                details = json.loads(event['details'])
                if 'current_database_list' in details :
                    drop_current_databases(details['current_database_list'],spec['staging_uri'],spec['tgt_uri'])
        get_logger().info("Metadata load complete, Handover successful")
        spec['progress_complete']=3
        #get_logger().info("Metadata load complete, submitting event")
        #submit_event(spec,result)
    return

def submit_event(spec,result):
    """Submit an event"""
    print(result['output']['events'])
    for event in result['output']['events']:
        print(event)
        event_client.submit_job({"type":event['type'],"genome":event['genome']})
        get_logger().debug("Submitted event to event handler endpoint")

def drop_current_databases(current_db_list,staging_uri,tgt_uri):
    """Drop databases on a previous assembly or previous genebuild (e.g: Wormbase) from the staging MySQL server"""
    tgt_url=make_url(tgt_uri)
    #Check if the new database has the same name as the one on staging. In this case DO NOT drop it
    #This can happen if the assembly get renamed or genebuild version has changed for Wormbase
    if tgt_url.database in current_db_list:
        get_logger().debug("The assembly or genebuild has been updated but the new database " + str(tgt_url.database) +" is the same as old one")
    else:
        for database in current_db_list:
            db_uri = staging_uri + database
            if database_exists(db_uri):
                get_logger().info("Dropping " + str(db_uri))
                drop_database(db_uri)
    return
