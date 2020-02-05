'''
@author: dstaines
'''
from ensembl_prodinf.event_celery_app import app
from ensembl_prodinf.event_client import EventClient

import event_config as cfg
from ensembl_prodinf import reporting
import json

event_client = EventClient(cfg.event_uri)

pool = reporting.get_pool(cfg.report_server)

def get_logger():
    """Obtain a logger from the reporting module that can write persistent reports"""
    return reporting.get_logger(pool, cfg.report_exchange, 'event_processing', None, {})

@app.task(bind=True)
def process_result(self, event, process, job_id):
    """
    Wait for the completion of the job and then process any output further
    """
    reporting.set_logger_context(get_logger(), event['genome'], event)

    # allow infinite retries
    self.max_retries = None
    get_logger().info("Checking {} event {}".format(process, job_id))
    result = event_client.retrieve_job(process, job_id)
    if (result['status'] == 'incomplete') or (result['status'] == 'running') or (result['status'] == 'submitted'):
        get_logger().info("Job incomplete, retrying")
        raise self.retry()

    get_logger().debug("Handling result for " + json.dumps(event))

    if result['status'] == 'failure':
        get_logger().fatal("Event failed: "+json.dumps(result))
    else:
        get_logger().info("Event succeeded: "+json.dumps(result))
        # TODO
        # 1. update metadata
        # 2. schedule new events as required

    return event['event_id']
