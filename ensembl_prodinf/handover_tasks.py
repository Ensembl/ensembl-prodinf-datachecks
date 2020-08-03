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

import logging
import json
import uuid
import re

from ensembl_prodinf.handover_celery_app import app

from ensembl_prodinf.db_copy_client import DbCopyClient
from ensembl_prodinf.metadata_client import MetadataClient
from ensembl_prodinf.event_client import EventClient
from ensembl.datacheck.client import DatacheckClient
from sqlalchemy_utils.functions import database_exists, drop_database
from sqlalchemy.engine.url import make_url
from ensembl_prodinf.utils import send_email
from ensembl_prodinf.models.compara import check_grch37, get_release_compara
from ensembl_prodinf.models.core import get_division, get_release
from ensembl_prodinf import handover_config as cfg
from ensembl_prodinf import reporting
from ensembl_prodinf.amqp_publishing import AMQPPublisher
from ensembl_prodinf.reporting import make_report, ReportFormatter
import handover_config

retry_wait = app.conf.get('retry_wait',60)
release = int(handover_config.RELEASE)



retry_wait = app.conf.get('retry_wait',60)
db_copy_client = DbCopyClient(cfg.copy_uri)
metadata_client = MetadataClient(cfg.meta_uri)
event_client = EventClient(cfg.event_uri)
dc_client = DatacheckClient(cfg.dc_uri)

db_types_list = [i for i in cfg.allowed_database_types.split(",")]
allowed_divisions_list = [i for i in cfg.allowed_divisions.split(",")]
species_pattern = re.compile(r'^(?P<prefix>\w+)_(?P<type>core|rnaseq|cdna|otherfeatures|variation|funcgen)(_\d+)?_(\d+)_(?P<assembly>\d+)$')
compara_pattern = re.compile(r'^ensembl_compara(_(?P<division>[a-z]+|pan)(_homology)?)?(_(\d+))?(_\d+)$')
ancestral_pattern = re.compile(r'^ensembl_ancestral(_(?P<division>[a-z]+))?(_(\d+))?(_\d+)$')
blat_species = ['homo_sapiens',
                'mus_musculus',
                'danio_rerio',
                'rattus_norvegicus',
                'gallus_gallus',
                'canis_lupus_familiaris',
                'bos_taurus',
                'oryctolagus_cuniculus',
                'oryzias_latipes',
                'sus_scrofa',
                'meleagris_gallopavo',
                'anas_platyrhynchos_platyrhynchos',
                'ovis_aries',
                'oreochromis_niloticus',
                'gadus_morhua']

logger = logging.getLogger(__name__)

handover_formatter = ReportFormatter('handover')
publisher = AMQPPublisher(cfg.report_server,
                          cfg.report_exchange,
                          exchange_type=cfg.report_exchange_type,
                          formatter=handover_formatter)


def log_and_publish(report):
    """Handy function to mimick the logger/publisher behaviour.
    """
    level = report['report_type']
    routing_key = 'report.%s' % level.lower()
    logger.log(getattr(logging, level), report['msg'])
    publisher.publish(report, routing_key)


def handover_database(spec):
    """ Method to accept a new database for incorporation into the system
    Argument is a dict with the following keys:
    * src_uri - URI to database to handover (required)
    * tgt_uri - URI to copy database to (optional - generated from staging and src_uri if not set)
    * contact - email address of submitter (required)
    * comment - additional information about submission (required)
    The following keys are added during the handover process:
    * handover_token - unique identifier for this particular handover invocation
    * dc_job_id - job ID for datacheck process
    * db_job_id - job ID for database copy process
    * metadata_job_id - job ID for the metadata loading process
    * progress_total - Total number of task to do
    * progress_complete - Total number of task completed
    """
    # TODO verify dict
    src_uri = spec['src_uri']
    # create unique identifier
    spec['handover_token'] = str(uuid.uuid1())
    spec['progress_total'] = 3
    if not database_exists(src_uri):
        msg = "Handover failed, %s does not exist" % src_uri
        log_and_publish(make_report('ERROR', msg, spec, src_uri))
        raise ValueError("%s does not exist" % src_uri)
    src_url = make_url(src_uri)
    #Scan database name and retrieve species or compara name, database type, release number and assembly version
    db_prefix, db_type, assembly = parse_db_infos(src_url.database)
    # Check if the given database can be handed over
    if db_type not in db_types_list:
        msg = "Handover failed, %s has been handed over after deadline. Please contact the Production team" % src_uri
        log_and_publish(make_report('ERROR', msg, spec, src_uri))
        raise ValueError(msg)
    # Check if the database release match the handover service
    if db_type == 'compara':
        compara_release = get_release_compara(src_uri)
        if release != compara_release:
            msg = "Handover failed, %s database release version %s does not match handover service release version %s" % (src_uri,compara_release,release)
            log_and_publish(make_report('ERROR', msg, spec, src_uri))
            raise ValueError(msg)
    else:
        db_release=get_release(src_uri)
        if release != db_release:
            msg = "Handover failed, %s database release version %s does not match handover service release version %s" % (src_uri,db_release,release)
            log_and_publish(make_report('ERROR', msg, spec, src_uri))
            raise ValueError(msg)
    #Check to which staging server the database need to be copied to
    spec, staging_uri, live_uri = check_staging_server(spec, db_type, db_prefix, assembly)
    if 'tgt_uri' not in spec:
        spec['tgt_uri'] = get_tgt_uri(src_url, staging_uri)
    # Check that the database division match the target staging server
    if db_type in ['compara', 'ancestral']:
        db_division = db_prefix
    else:
        db_division = get_division(src_uri, spec['tgt_uri'], db_type)
    if db_division not in allowed_divisions_list:
        raise ValueError('Database division %s does not match server division list %s' % (db_division, allowed_divisions_list))
    spec['staging_uri'] = staging_uri
    spec['progress_complete'] = 0
    msg = "Handling %s" % spec
    log_and_publish(make_report('INFO', msg, spec, src_uri))
    submit_dc(spec, src_url, db_type)
    return spec['handover_token']


def get_tgt_uri(src_url, staging_uri):
    """Create target URI from staging details and name of source database"""
    return '%s%s' % (staging_uri, src_url.database)


def parse_db_infos(database):
    """Parse database name and extract db_prefix and db_type. Also extract release and assembly for species databases"""
    if species_pattern.match(database):
        m = species_pattern.match(database)
        db_prefix = m.group('prefix')
        db_type = m.group('type')
        assembly = m.group('assembly')
        return db_prefix, db_type, assembly
    elif compara_pattern.match(database):
        m = compara_pattern.match(database)
        division = m.group('division')
        db_prefix = division if division else 'vertebrates'
        return db_prefix, 'compara', None
    elif ancestral_pattern.match(database):
        m = ancestral_pattern.match(database)
        division = m.group('division')
        db_prefix = division if division else 'vertebrates'
        return db_prefix, 'ancestral', None
    else:
        raise ValueError("Database type for %s is not expected. Please contact the Production team" % database)


def check_staging_server(spec,db_type,db_prefix,assembly):
    """Find which staging server should be use. secondary_staging for GRCh37 and Bacteria, staging for the rest"""
    if 'bacteria' in db_prefix:
        staging_uri = cfg.secondary_staging_uri
        live_uri = cfg.secondary_live_uri
    elif db_prefix == 'homo_sapiens' and assembly == '37':
        staging_uri = cfg.secondary_staging_uri
        live_uri = cfg.secondary_live_uri
        spec['GRCh37'] = 1
        spec['progress_total'] = 2
    elif db_type == 'compara' and check_grch37(spec['src_uri'], 'homo_sapiens'):
        staging_uri = cfg.secondary_staging_uri
        live_uri = cfg.secondary_live_uri
        spec['GRCh37'] = 1
        spec['progress_total'] = 2
    else:
        staging_uri = cfg.staging_uri
        live_uri = cfg.live_uri
    return spec, staging_uri, live_uri

def submit_dc(spec, src_url, db_type):
    """Submit the source database for checking. Returns a celery job identifier"""
    try:
        src_uri = spec['src_uri']
        tgt_uri = spec['tgt_uri']
        handover_token = spec['handover_token']
        server_url = 'mysql://%s@%s:%s/' % (src_url.username, src_url.host, src_url.port)
        submitting_dc_msg = 'Submitting DC for %s on server: %s' % (src_url.database, server_url)
        submitting_dc_report = make_report('DEBUG', submitting_dc_msg, spec, src_uri)
        if db_type == 'compara':
            log_and_publish(submitting_dc_report)
            dc_job_id = dc_client.submit_job(server_url, src_url.database, None, None,
                    db_type, None, db_type, 'critical', None, handover_token)
        elif db_type == 'ancestral':
            log_and_publish(submitting_dc_report)
            dc_job_id = dc_client.submit_job(server_url, src_url.database, None, None,
                    'core', None, 'ancestral', 'critical', None, handover_token)
        elif db_type in ['rnaseq', 'cdna', 'otherfeatures']:
            division_msg = 'division: %s' % get_division(src_uri, tgt_uri, db_type)
            log_and_publish(make_report('DEBUG', division_msg, spec, src_uri))
            log_and_publish(submitting_dc_report)
            dc_job_id = dc_client.submit_job(server_url, src_url.database, None, None,
                    db_type, None, 'corelike', 'critical', None, handover_token)
        else:
            db_msg = 'src_uri: %s dbtype %s server_url %s' % (src_uri, db_type, server_url)
            log_and_publish(make_report('DEBUG', db_msg, spec, src_uri))
            division_msg = 'division: %s' % get_division(src_uri, tgt_uri, db_type)
            log_and_publish(make_report('DEBUG', division_msg, spec, src_uri))
            log_and_publish(submitting_dc_report)
            dc_job_id = dc_client.submit_job(server_url, src_url.database, None, None,
                    db_type, None, db_type, 'critical', None, handover_token)
    except Exception as e:
        err_msg = 'Handover failed, Cannot submit dc job'
        log_and_publish(make_report('ERROR', err_msg, spec, src_uri))
        raise ValueError('Handover failed, Cannot submit dc job %s' % e) from e
    spec['dc_job_id'] = dc_job_id
    task_id = process_datachecked_db.delay(dc_job_id, spec)
    submitted_dc_msg = 'Submitted DB for checking as %s' % task_id
    log_and_publish(make_report('DEBUG', submitted_dc_msg, spec, src_uri))
    return task_id


@app.task(bind=True, default_retry_delay=retry_wait)
def process_datachecked_db(self, dc_job_id, spec):
    """ Task to wait until DCs finish and then respond e.g.
    * submit copy if DC succeed
    * send error email if not
    """
    # allow infinite retries
    self.max_retries = None
    src_uri = spec['src_uri']
    progress_msg = 'Datachecks in progress, please see: %sjobs/%s' % (cfg.dc_uri, dc_job_id)
    log_and_publish(make_report('INFO', progress_msg, spec, src_uri))
    try:
        result = dc_client.retrieve_job(dc_job_id)
    except Exception as e:
        err_msg = 'Handover failed, cannot retrieve datacheck job'
        log_and_publish(make_report('ERROR', err_msg, spec, src_uri))
        raise ValueError('Handover failed, cannot retrieve datacheck job %s' % e) from e
    if result['status'] in ['incomplete', 'running', 'submitted']:
        log_and_publish(make_report('DEBUG', 'Datacheck Job incomplete, checking again later', spec, src_uri))
        raise self.retry()
    # check results
    elif result['status'] == 'failed':
        prob_msg = 'Datachecks found problems, you can download the output here: %sdownload_datacheck_outputs/%s' % (cfg.dc_uri, dc_job_id)
        log_and_publish(make_report('INFO', prob_msg, spec, src_uri))
        msg = """
Running datachecks on %s completed but found problems.
You can download the output here %s
""" % (src_uri, cfg.dc_uri + "download_datacheck_outputs/" + str(dc_job_id))
        send_email(to_address=spec['contact'], subject='Datacheck found problems', body=msg, smtp_server=cfg.smtp_server)
    else:
        log_and_publish(make_report('INFO', 'Datachecks successful, starting copy', spec, src_uri))
        spec['progress_complete'] = 1
        submit_copy(spec)


def submit_copy(spec):
    """Submit the source database for copying to the target. Returns a celery job identifier"""
    src_uri = spec['src_uri']
    try:
        copy_job_id = db_copy_client.submit_job(src_uri, spec['tgt_uri'], None, None,
                                                False, True, True, None, None)
    except Exception as e:
        log_and_publish(make_report('ERROR', 'Handover failed, cannot submit copy job', spec, src_uri))
        raise ValueError('Handover failed, cannot submit copy job %s' % e) from e
    spec['copy_job_id'] = copy_job_id
    task_id = process_copied_db.delay(copy_job_id, spec)
    dbg_msg = 'Submitted DB for copying as %s' % task_id
    log_and_publish(make_report('DEBUG', 'Handover failed, cannot submit copy job', spec, src_uri))
    return task_id


@app.task(bind=True, default_retry_delay=retry_wait)
def process_copied_db(self, copy_job_id, spec):
    """Wait for copy to complete and then respond accordingly:
    * if success, submit to metadata database
    * if failure, flag error using email"""
    # allow infinite retries
    self.max_retries = None
    src_uri = spec['src_uri']
    copy_in_progress_msg = 'Copying in progress, please see: %s%s' % (cfg.copy_web_uri, copy_job_id)
    log_and_publish(make_report('INFO', copy_in_progress_msg, spec, src_uri))
    try:
        result = db_copy_client.retrieve_job(copy_job_id)
    except Exception as e:
        log_and_publish(make_report('ERROR', 'Handover failed, cannot retrieve copy job', spec, src_uri))
        raise ValueError('Handover failed, cannot retrieve copy job %s' % e) from e
    if result['status'] in ['incomplete', 'running', 'submitted']:
        log_and_publish(make_report('DEBUG', 'Database copy job incomplete, checking again later', spec, src_uri))
        raise self.retry()
    if result['status'] == 'failed':
        copy_failed_msg = 'Copy failed, please see: %s%s' % (cfg.copy_web_uri, copy_job_id)
        log_and_publish(make_report('INFO', copy_failed_msg, spec, src_uri))
        msg = """
Copying %s to %s failed.
Please see %s
""" % (src_uri, spec['tgt_uri'], cfg.copy_web_uri + str(copy_job_id))
        send_email(to_address=spec['contact'], subject='Database copy failed', body=msg, smtp_server=cfg.smtp_server)
        return
    elif 'GRCh37'in spec:
        log_and_publish(make_report('INFO', 'Copying complete, Handover successful', spec, src_uri))
        spec['progress_complete'] = 2
    else:
        log_and_publish(make_report('INFO', 'Copying complete, submitting metadata job', spec, src_uri))
        spec['progress_complete'] = 2
        submit_metadata_update(spec)


def submit_metadata_update(spec):
    """Submit the source database for copying to the target. Returns a celery job identifier."""
    src_uri = spec['src_uri']
    try:
        metadata_job_id = metadata_client.submit_job(spec['tgt_uri'], None, None, None,
                None, spec['contact'], spec['comment'], 'Handover', None)
    except Exception as e:
        log_and_publish(make_report('ERROR', 'Handover failed, cannot submit metadata job', spec, src_uri))
        raise ValueError('Handover failed, cannot submit metadata job %s' % e) from e
    spec['metadata_job_id'] = metadata_job_id
    task_id = process_db_metadata.delay(metadata_job_id, spec)
    dbg_msg = 'Submitted DB for metadata loading %s' % task_id
    log_and_publish(make_report('DEBUG', dbg_msg, spec, src_uri))
    return task_id


@app.task(bind=True, default_retry_delay=retry_wait)
def process_db_metadata(self, metadata_job_id, spec):
    """Wait for metadata update to complete and then respond accordingly:
    * if success, submit event to event handler for further processing
    * if failure, flag error using email"""
    # allow infinite retries
    self.max_retries = None
    tgt_uri = spec['tgt_uri']
    loading_msg = 'Loading into metadata database, please see: %sjobs/%s' % (cfg.meta_uri, metadata_job_id)
    log_and_publish(make_report('INFO', loading_msg, spec, tgt_uri))
    try:
        result = metadata_client.retrieve_job(metadata_job_id)
    except Exception as e:
        err_msg = 'Handover failed, Cannot retrieve metadata job'
        log_and_publish(make_report('ERROR', err_msg, spec, tgt_uri))
        raise ValueError('Handover failed, Cannot retrieve metadata job %s' % e) from e
    if result['status'] in ['incomplete', 'running', 'submitted']:
        incomplete_msg = 'Metadata load Job incomplete, checking again later'
        log_and_publish(make_report('DEBUG', incomplete_msg, spec, tgt_uri))
        raise self.retry()
    if result['status'] == 'failed':
        drop_msg='Dropping %s' % tgt_uri
        log_and_publish(make_report('INFO', drop_msg, spec, tgt_uri))
        drop_database(spec['tgt_uri'])
        failed_msg = 'Metadata load failed, please see %sjobs/%s?format=failures' % (cfg.meta_uri, metadata_job_id)
        log_and_publish(make_report('INFO', failed_msg, spec, tgt_uri))
        msg = """
Metadata load of %s failed.
Please see %s
""" % (tgt_uri, cfg.meta_uri + 'jobs/' + str(metadata_job_id) + '?format=failures')
        send_email(to_address=spec['contact'], subject='Metadata load failed, please see: '+cfg.meta_uri+ 'jobs/' + str(metadata_job_id) + '?format=failures', body=msg, smtp_server=cfg.smtp_server)
    else:
        # Cleaning up old assembly or old genebuild databases for Wormbase when database suffix has changed
        if 'events' in result['output'] and result['output']['events']:
            for event in result['output']['events']:
                details = json.loads(event['details'])
                if 'current_database_list' in details :
                    drop_current_databases(details['current_database_list'], spec)
                if event['genome'] in blat_species and event['type'] == 'new_assembly':
                    msg = 'The following species %s has a new assembly, please update the port number for this species here and communicate to Web: https://github.com/Ensembl/ensembl-production/blob/master/modules/Bio/EnsEMBL/Production/Pipeline/PipeConfig/DumpCore_conf.pm#L107' % event['genome']
                    send_email(to_address=cfg.production_email,
                               subject='BLAT species list needs updating in FTP Dumps config',
                               body=msg)
        log_and_publish(make_report('INFO', 'Metadata load complete, Handover successful', spec, tgt_uri))
        spec['progress_complete'] = 3
        #log_and_publish(make_report('INFO', 'Metadata load complete, submitting event', spec, tgt_uri))
        #submit_event(spec,result)


def submit_event(spec, result):
    """Submit an event"""
    tgt_uri = spec['tgt_uri']
    logger.debug(result['output']['events'])
    for event in result['output']['events']:
        logger.debug(event)
        event_client.submit_job({'type': event['type'], 'genome': event['genome']})
        log_and_publish(make_report('DEBUG', 'Submitted event to event handler endpoint', spec, tgt_uri))


def drop_current_databases(current_db_list, spec):
    """Drop databases on a previous assembly or previous genebuild (e.g: Wormbase) from the staging MySQL server"""
    tgt_uri = spec['tgt_uri']
    staging_uri = spec['staging_uri']
    tgt_url = make_url(tgt_uri)
    #Check if the new database has the same name as the one on staging. In this case DO NOT drop it
    #This can happen if the assembly get renamed or genebuild version has changed for Wormbase
    if tgt_url.database in current_db_list:
        msg = 'The assembly or genebuild has been updated but the new database %s is the same as old one' % tgt_url.database
        log_and_publish(make_report('DEBUG', msg, spec, tgt_uri))
    else:
        for database in current_db_list:
            db_uri = staging_uri + database
            if database_exists(db_uri):
                msg = 'Dropping %s' % db_uri
                log_and_publish(make_report('INFO', msg, spec, tgt_uri))
                drop_database(db_uri)
