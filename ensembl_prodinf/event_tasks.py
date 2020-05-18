'''
@author: dstaines
'''
import json
import logging

from ensembl_prodinf.event_celery_app import app
from ensembl_prodinf.event_client import EventClient

import event_config as cfg
from ensembl_prodinf.amqp_publishing import AMQPPublisher
from ensembl_prodinf.reporting import make_report, ReportFormatter

event_client = EventClient(cfg.event_uri)

logger = logging.getLogger(__name__)

event_formatter = ReportFormatter('event_processing')
publisher = AMQPPublisher(cfg.report_server, cfg.report_exchange, formatter=event_formatter)


def log_and_publish(report):
    level = report['report_type']
    routing_key = 'report.%s' % level.lower()
    logger.log(level, report['msg'])
    publisher.publish(report, routing_key)


@app.task(bind=True)
def process_result(self, event, process, job_id):
    """
    Wait for the completion of the job and then process any output further
    """

    # allow infinite retries
    self.max_retries = None
    genome = event['genome']
    checking_msg ='Checking %s event %s' % (process, job_id)
    log_and_publish(make_report('INFO', checking_msg, event, genome))
    result = event_client.retrieve_job(process, job_id)
    if (result['status'] == 'incomplete') or (result['status'] == 'running') or (result['status'] == 'submitted'):
        log_and_publish(make_report('INFO', 'Job incomplete, retrying', event, genome))
        raise self.retry()
    result_msg = 'Handling result for %s' % json.dumps(event)
    log_and_publish(make_report('DEBUG', 'Job incomplete, retrying', event, genome))
    result_dump = json.dumps(result)
    if result['status'] == 'failure':
        log_and_publish(make_report('FATAL', 'Event failed: %s' % result_dump, event, genome))
    else:
        log_and_publish(make_report('INFO', 'Event succeeded: %s' % result_dump, event, genome))
        # TODO
        # 1. update metadata
        # 2. schedule new events as required

    return event['event_id']
