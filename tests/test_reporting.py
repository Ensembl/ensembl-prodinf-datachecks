# -*- coding: utf-8 -*-

import logging
import unittest
import threading
import json
from ensembl_prodinf.reporting import ContextFilter, JsonFormatter

logging.basicConfig()

class UtilsTest(unittest.TestCase):

    def test_filter(self):
        
        context = threading.local() 
        context.host = "myhost"
        context.process = "myprocess"
        context.resource = "myres"
        f = ContextFilter(context)
        msg = "Hello world"
        record = logging.LogRecord("logger", "INFO", None, "1", msg, None, None, None)
        result = f.filter(record)
        self.assertTrue(result, "Checking filter return")
        self.assertEquals(record.host, context.host)
        self.assertEquals(record.process, context.process)
        self.assertEquals(record.resource, context.resource)
        self.assertEquals(record.msg, msg)
        context.process = "mynewprocess"
        msg = "Goodbye world"
        record = logging.LogRecord("logger", "INFO", None, "1", msg, None, None, None)
        result = f.filter(record)
        self.assertTrue(result, "Checking filter return")
        self.assertEquals(record.host, context.host)
        self.assertEquals(record.process, context.process)
        self.assertEquals(record.resource, context.resource)
        self.assertEquals(record.msg, msg)

    def test_formatter(self):
        
        msg = "Hello world"
        record = logging.LogRecord("logger", 20, None, "1", msg, None, None, None)
        record.host = "myhost"
        record.process = "myprocess"
        record.resource = "myres"
        record.report_time = "2017-01-01T06:00:01"
        record.params = {"key":"val"}
        print record.levelname
        f = JsonFormatter()
        json_str = f.format(record)
        report = json.loads(json_str)
        self.assertEquals(record.host, report['host'])
        self.assertEquals(record.process, report['process'])
        self.assertEquals(record.resource, report['resource'])
        self.assertEquals(record.report_time, report['report_time'])
        self.assertDictEqual(record.params, report['params'])
