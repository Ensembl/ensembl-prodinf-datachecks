import logging
import unittest
# import threading
# import json
# from ensembl_prodinf.reporting import ContextFilter, JsonFormatter
from ensembl_prodinf.reporting import make_report, ReportFormatter

logging.basicConfig()

class UtilsTest(unittest.TestCase):
    #  def test_filter(self):
    #      context = {
    #        'host' : "myhost",
    #        'process' : "myprocess",
    #        'resource' : "myres"
    #      }

    #      f = ContextFilter(context)
    #      msg = "Hello world"
    #      record = logging.LogRecord("logger", 20, None, "1", msg, None, None, None)
    #      print(record.levelname)
    #      result = f.filter(record)
    #      self.assertTrue(result, "Checking filter return")
    #      self.assertEqual(record.host, context['host'])
    #      self.assertEqual(record.process, context['process'])
    #      self.assertEqual(record.resource, context['resource'])
    #      self.assertEqual(record.msg, msg)
    #      context['process'] = "mynewprocess"
    #      msg = "Goodbye world"
    #      record = logging.LogRecord("logger", 20, None, "1", msg, None, None, None)
    #      result = f.filter(record)
    #      self.assertTrue(result, "Checking filter return")
    #      self.assertEqual(record.host, context['host'])
    #      self.assertEqual(record.process, context['process'])
    #      self.assertEqual(record.resource, context['resource'])
    #      self.assertEqual(record.msg, msg)

    #  def test_formatter(self):
    #      msg = "Hello world"
    #      record = logging.LogRecord("logger", 20, None, "1", msg, None, None, None)
    #      record.host = "myhost"
    #      record.process = "myprocess"
    #      record.resource = "myres"
    #      record.report_time = "2017-01-01T06:00:01"
    #      record.params = {"key":"val"}
    #      print(record.levelname)
    #      f = JsonFormatter()
    #      json_str = f.format(record)
    #      report = json.loads(json_str)
    #      self.assertEqual(record.host, report['host'])
    #      self.assertEqual(record.process, report['process'])
    #      self.assertEqual(record.resource, report['resource'])
    #      self.assertEqual(record.report_time, report['report_time'])
    #      self.assertDictEqual(record.params, report['params'])

    def test_make_report(self):
        expected = {
            'params': {'test_param': 'test'},
            'resource': 'test_resource',
            'report_type': 'TEST',
            'msg': 'test_message'
        }
        report = make_report('TEST', 'test_message', {'test_param': 'test'}, 'test_resource')
        self.assertEqual(expected, report)

    def test_report_formatter(self):
        report = {
            'params': {'test_param': 'test'},
            'resource': 'test_resource',
            'report_type': 'TEST',
            'msg': 'test_message'
        }
        expected_subset = {
            'report_type': 'TEST',
            'process': 'test_process',
            'resource': 'test_resource',
            'params': {'test_param': 'test'},
            'message': 'test_message'
        }
        report_null = {
            'report_type': 'TEST',
        }
        expected_null = {
            'report_type': 'TEST',
            'process': 'test_process',
            'resource': '',
            'params': {},
            'message': ''
        }
        formatter = ReportFormatter('test_process')
        result = formatter.format(report)
        self.assertDictContainsSubset(expected_subset, result)
        date_re = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}'
        date = result['report_time']
        self.assertRegex(date, date_re)
        result_null = formatter.format(report_null)
        self.assertDictContainsSubset(expected_null, result_null)
        self.assertRaises(ValueError, formatter.format, {})


