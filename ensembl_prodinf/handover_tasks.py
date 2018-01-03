'''
Created on 4 Dec 2017

@author: dstaines
'''
from ensembl_prodinf.handover_celery_app import app
import logging
import db_copy_client
import hc_client
from sqlalchemy_utils.functions import database_exists
from sqlalchemy.engine.url import make_url
from .utils import send_email
import handover_config as cfg
import uuid        

        
def handover_database(spec):    
    logging.info("Handling " + str(spec))
    if 'tgt_uri' not in spec:
        spec['tgt_uri'] = get_tgt_uri(spec['src_uri'])
    spec['handover_token'] = str(uuid.uuid1())                    
    check_db(spec['src_uri'])
    check_registry(spec)     
    hc_job_id = submit_hc(spec['src_uri'])    
    spec['hc_job_id'] = hc_job_id
    task_id = process_checked_db.delay(hc_job_id, spec)
    logging.debug("Submitted DB for checking as " + str(task_id))
    send_email(to_address=spec['contact'], subject='HC submitted', body=str(spec['src_uri']) + ' has been submitted for checking', smtp_server=cfg.smtp_server)
    return spec['handover_token']

def get_tgt_uri(src_uri):
    url = make_url(src_uri)
    return str(cfg.staging_uri) + str(url.database)
    
def check_db(uri):    
    if(database_exists(uri) == False):
        logging.error(uri + " does not exist")
        raise ValueError(uri + " does not exist")
    else:
        logging.info(uri + " looks good to me")
        return


def check_registry(spec):
    logging.info(spec['src_uri'] + " looks good to el reg")
    return

    
def submit_hc(uri):
    return hc_client.submit_job(cfg.hc_uri, uri, cfg.production_uri, cfg.compara_uri, cfg.staging_uri, cfg.live_uri, None, cfg.handover_group)


@app.task(bind=True)
def process_checked_db(self, hc_job_id, spec):
    """ Task to wait until HCs finish and then respond
    """
    
    # allow infinite retries 
    self.max_retries = None
    logging.info("Checking HCs for " + spec['src_uri'] + " from job " + str(hc_job_id))
    result = hc_client.retrieve_job(cfg.hc_uri, hc_job_id)
    if (result['status'] == 'incomplete') or (result['status'] == 'running') or (result['status'] == 'submitted'):
        logging.info("Job incomplete, retrying")
        raise self.retry()
    
    # check results
    if (result['status'] == 'failed'):
        logging.info("HCs failed to run")    
        msg = """
Running healthchecks vs %s failed to execute.
Please see %s
""" % (spec['src_uri'], cfg.hc_web_uri + str(hc_job_id))
        send_email(to_address=spec['contact'], subject='HC failed to run', body=msg, smtp_server=cfg.smtp_server)         
        return 
    elif (result['output']['status'] == 'failed'):
        logging.info("HCs found problems")
        msg = """
Running healthchecks vs %s completed but found failures.
Please see %s
""" % (spec['src_uri'], cfg.hc_web_uri + str(hc_job_id))
        send_email(to_address=spec['contact'], subject='HC ran but failed', body=msg, smtp_server=cfg.smtp_server)  
        return
    else:
        logging.info("HCs fine, starting copy")
        copy_job_id = submit_copy(spec['src_uri'], spec['tgt_uri'])
        spec['copy_job_id'] = copy_job_id
        task_id = process_copied_db.delay(copy_job_id, spec)    
        logging.debug("Submitted DB for checking as " + str(task_id))
        return task_id


def submit_copy(src_uri, tgt_uri):
    return db_copy_client.submit_job(cfg.copy_uri, src_uri, tgt_uri, None, None, False, True)


@app.task(bind=True)    
def process_copied_db(self, copy_job_id, spec):
    # allow infinite retries 
    self.max_retries = None
    logging.info("Checking " + str(spec) + " using " + str(copy_job_id))
    result = db_copy_client.retrieve_job(cfg.copy_uri, copy_job_id)
    if (result['status'] == 'incomplete') or (result['status'] == 'running') or (result['status'] == 'submitted'):
        logging.info("Job incomplete, retrying")
        raise self.retry() 
    
    if (result['status'] == 'failed'):
        logging.info("Copy failed")
        msg = """
Copying %s to %s failed.
Please see %s
""" % (spec['src_uri'], spec['tgt_uri'], cfg.copy_web_uri + str(copy_job_id))
        send_email(to_address=spec['contact'], subject='Database copy failed', body=msg, smtp_server=cfg.smtp_server)          
        return
    else:
        logging.info("Copying complete, need to submit metadata")
        meta_job_id = submit_metadata_update(spec['tgt_uri'])
        task_id = process_db_metadata.delay(meta_job_id, spec)    
        logging.debug("Submitted DB for meta update as " + str(task_id))
        return task_id
    

def submit_metadata_update(uri):
    return 'metaplaceholder_db_id'


@app.task(bind=True)    
def process_db_metadata(self, meta_job_id, spec):
    logging.info("Assuming completed meta update " + str(meta_job_id))
    # TODO
    return
