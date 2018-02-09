import json
from logging import Handler
import logging
from time import gmtime, strftime
import pika

binding_keys = {
                    'CRITICAL':'report.fatal',
                    'ERROR':'report.error',
                    'INFO':'report.info',
                    'DEBUG':'report.debug',
                    'WARN':'report.warn'
                   }

class ContextFilter(logging.Filter):

    def __init__(self, context):
        self.context = context

    def filter(self, record):
        record.host = self.context.host
        record.process = self.context.process
        record.resource = self.context.resource
        record.report_time = strftime("%Y-%m-%dT%H:%M:%S", gmtime())
        record.report_type = binding_keys[record.levelname]
        if hasattr(self.context, 'params'):
            record.params = self.context.params
        else:
            record.params = {}            
        return True

class JsonFormatter(logging.Formatter):
        
    def format(self, record):
        obj = {
            "report_type":record.report_type,
            "host":record.host,
            "process":record.process,
            "resource":record.resource,
            "params":record.params,
            "report_time":record.report_time,
            "message":record.msg
            }
        return json.dumps(obj)


class QueueAppenderHandler(Handler):
    
    def __init__(self, queue_url, exchange):
        Handler.__init__(self)
        connection = pika.BlockingConnection(pika.URLParameters(queue_url))
        self.channel = connection.channel()
        self.exchange = exchange
    
    def emit(self, record):
        record_json = self.format(record)
        self.channel.basic_publish(exchange=self.exchange,
                      routing_key=record.report_type,
                      body=record_json)
        return True
