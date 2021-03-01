import unittest
from ensembl_prodinf.reporting import make_report, ReportFormatter


class UtilsTest(unittest.TestCase):
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


