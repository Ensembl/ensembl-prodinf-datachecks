import logging
import socket
from datetime import datetime


_HOSTNAME = socket.gethostname()


reporting_logger = logging.getLogger(__name__)


def make_report(report_type, msg, params=None, resource=''):
    if params is None:
        params = {}
    return {
        'params': params,
        'resource': resource,
        'report_type': report_type,
        'msg': msg
    }


class ReportFormatter:
    def __init__(self, process_name):
        self.process_name = process_name

    def format(self, report):
        try:
            report_type = report['report_type']
        except KeyError:
            raise ValueError("Report: %s is missing report required field 'report_type'" % report)
        return {
            'report_type': report_type, # CRITICAL, ERROR, INFO, DEBUG, WARN
            'host': _HOSTNAME,
            'process': self.process_name,
            'resource': report.get('resource', ''),
            'params': report.get('params', {}),
            'report_time': datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3],
            'message': report.get('msg', '')
        }

