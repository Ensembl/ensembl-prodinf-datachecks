# import json
# from logging import Handler
import logging
# import threading
import socket
# from time import strftime
from datetime import datetime
# import pika
# import pika_pool

"""
Module which generates Python logger instances which send messages to RabbitMQ for further processing.
The main entry point should be get_logger().
RabbitMQ communication uses pooled Pika connections (pool obtained from get_pool())
Loggers contain additional context which is added to messages, namely:
      host : current host name
      process : name of process to tag messages with
      resource : name of active resource to tag messages with
      params : additional tags as a dict to tag messages with
"""

"""Binding from log level to a routing key for the queue exchange"""
#  binding_keys = {    # LEVEL: routing.key
#                      'CRITICAL':'report.fatal',
#                      'ERROR':'report.error',
#                      'INFO':'report.info',
#                      'DEBUG':'report.debug',
#                      'WARN':'report.warn'
#                     }

#  thread_instance = threading.local()
#  thread_instance.logger = None

#  class ContextFilter(logging.Filter):
#      """Filter for use by logging package that adds context to a report"""

#      def __init__(self, context):
#          self.context = context

#      def filter(self, record):
#          record.host = self.context['host']
#          record.process = self.context['process']
#          record.resource = self.context['resource']
#          record.report_time = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]
#          record.report_type = binding_keys[record.levelname]
#          if 'params' in self.context.keys():
#              record.params = self.context['params']
#          else:
#              record.params = {}
#          return True


#  class JsonFormatter(logging.Formatter):
#      """Class for use by logging package that transforms a dict into JSON for sending to a queue"""

#      def format(self, record):
#          obj = {
#              "report_type":record.levelname,
#              "host":record.host,
#              "process":record.process,
#              "resource":record.resource,
#              "params":record.params,
#              "report_time":record.report_time,
#              "message":record.msg
#              }
#          return json.dumps(obj)


#  class QueueAppenderHandler(Handler):
#      """Class for use by logging package that appends messages to queues
#      """

#      def __init__(self, pool, exchange):
#          Handler.__init__(self)
#          self.pool = pool
#          self.exchange = exchange

#      def emit(self, record):
#          record_json = self.format(record)
#          with self.pool.acquire() as cxn:
#              cxn.channel.basic_publish(
#                  body=record_json,
#                  exchange=self.exchange,
#                  routing_key=record.report_type,
#                  properties=pika.BasicProperties(
#                      content_type='application/json',
#                      content_encoding='utf-8',
#                      delivery_mode=2,
#                  )
#              )
#          return True


#  def get_logger(pool, exchange, process, resource, params):
#      """
#      Main method to obtain a logger which writes to the
#      Arguments:
#        pool : Pika pool (use get_pool())
#        exchange : rabbitMQ exchange
#        process : name of process to tag messages with
#        resource : name of active resource to tag messages with
#        params : additional tags as a dict to tag messages with
#      """
#      if(thread_instance.logger==None):
#          """Construct a new logger capable of talking to a queue"""
#          thread_instance.logger = logging.getLogger(process)
#          thread_instance.logger.setLevel(logging.DEBUG)
#          appender = _get_appender(pool, exchange, process)
#          thread_instance.logger.context = appender.context
#          thread_instance.logger.addHandler(appender)
#          set_logger_context(thread_instance.logger, resource, params)
#      return thread_instance.logger

#  def _get_appender(pool, exchange, process):
#      """Internal method to create a queue appender for the logger"""
#      appender = QueueAppenderHandler(pool, exchange)
#      appender.context = {
#          'host':socket.gethostname(),
#          'process':process
#      }
#      appender.addFilter(ContextFilter(appender.context))
#      appender.setFormatter(JsonFormatter())
#      return appender


#  def set_logger_context(logger, resource, params):
#      """Update logger with new resource and param details
#      Arguments:
#        logger : active logger
#        resource : name of active resource to tag messages with
#        params : additional tags as a dict to tag messages with
#      """
#      logger.context['resource'] = resource
#      logger.context['params'] = params


#  def get_pool(queue_url, **kwargs):

#      """
#      Get an instance of Pika pool. This is a pool of Pika connections which can be used to write messages to RabbitMQ.
#      Arguments:
#        queue_url : rabbit MQ URI
#      Options passed as named args include:
#          socket_timeout
#          connection_attempts
#          max_size
#          max_overflow
#          timeout
#          recycle
#          stale
#      """

#      options = {
#          'socket_timeout' : 10,
#          'connection_attempts' : 2,
#          'max_size' : 10,
#          'max_overflow' : 10,
#          'timeout' : 10,
#          'recycle' : 3600,
#          'stale' : 45
#      }

#      options.update(kwargs)

#      """Pika is not thread safe, but 1 connection per thread is wasteful so use a pool instead"""
#      params = pika.URLParameters(
#              queue_url
#              + '?socket_timeout=' + str(options['socket_timeout']) + '&connection_attempts=' + str(options['connection_attempts'])
#      )

#      return pika_pool.QueuedPool(
#              create=lambda: pika.BlockingConnection(parameters=params),
#              max_size=options['max_size'],
#              max_overflow=options['max_overflow'],
#              timeout=options['timeout'],
#              recycle=options['recycle'],
#              stale=options['stale']
#          )


_HOSTNAME = socket.gethostname()


reporting_logger = logging.getLogger(__name__)


def make_report(report_type, msg, spec=None, resource=''):
    if spec is None:
        spec = {}
    return {
        'params': spec,
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

