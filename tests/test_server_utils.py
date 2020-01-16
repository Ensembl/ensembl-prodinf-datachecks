import ensembl_prodinf.server_utils as su

import unittest
import logging

logging.basicConfig()

class ServerTest(unittest.TestCase):

    def test_status(self):
        status = su.get_status()
        logging.info(status)
        self.assertTrue("n_cpus" in status)
        self.assertTrue("load_1m" in status)
        self.assertTrue("load_5m" in status)
        self.assertTrue("load_15m" in status)
        self.assertTrue("memory_total_m" in status)
        self.assertTrue("memory_used_m" in status)
        self.assertTrue("memory_available_m" in status)
        self.assertTrue(status["memory_used_pct"]>=0)
        self.assertTrue(status["memory_used_pct"]<=100)

    def test_status_dir(self):
        status = su.get_status(dir_name="/")
        logging.info(status)
        self.assertTrue("n_cpus" in status)
        self.assertTrue("load_1m" in status)
        self.assertTrue("load_5m" in status)
        self.assertTrue("load_15m" in status)
        self.assertTrue("memory_total_m" in status)
        self.assertTrue("memory_used_m" in status)
        self.assertTrue("memory_available_m" in status)
        self.assertTrue(status["memory_used_pct"]>=0)
        self.assertTrue(status["memory_used_pct"]<=100)
        self.assertTrue("disk_total_g" in status)
        self.assertTrue("disk_used_g" in status)
        self.assertTrue("disk_available_g" in status)
        self.assertTrue(status["disk_used_pct"]>=0)
        self.assertTrue(status["disk_used_pct"]<=100)


class AssertTest(unittest.TestCase):

    def test_raises_assert_http_uri(self):
        self.assertRaises(ValueError, su.assert_http_uri, '')
        self.assertRaises(ValueError, su.assert_http_uri, 'invalid_uri')
        self.assertRaises(ValueError, su.assert_http_uri, 'http://uri-with-no-slash')
        self.assertRaises(ValueError, su.assert_http_uri, 'mysql://wrong-schema')

    def test_passes_assert_http_uri(self):
        su.assert_http_uri('http://server-name/')
        su.assert_http_uri('https://server-name:port/')

    def test_raises_assert_mysql_uri(self):
        self.assertRaises(ValueError, su.assert_mysql_uri, '')
        self.assertRaises(ValueError, su.assert_mysql_uri, 'invalid_uri')
        self.assertRaises(ValueError, su.assert_mysql_uri, 'http://wrong_schema')
        self.assertRaises(ValueError, su.assert_mysql_uri, 'mysql://invalid')
        self.assertRaises(ValueError, su.assert_mysql_uri, 'mysql://user@server-no-slash')
        self.assertRaises(ValueError, su.assert_mysql_uri, 'mysql://user:pass@server-no-port/')

    def test_passes_assert_mysql_uri(self):
        su.assert_mysql_uri('mysql://user@server:3006/')
        su.assert_mysql_uri('mysql://user:pass@server:3306/')

    def test_raises_assert_mysql_db_uri(self):
        self.assertRaises(ValueError, su.assert_mysql_db_uri, '')
        self.assertRaises(ValueError, su.assert_mysql_db_uri, 'invalid_uri')
        self.assertRaises(ValueError, su.assert_mysql_db_uri, 'http://wrong_schema')
        self.assertRaises(ValueError, su.assert_mysql_db_uri, 'mysql://invalid')
        self.assertRaises(ValueError, su.assert_mysql_db_uri, 'mysql://user:pass@server-no-slash')
        self.assertRaises(ValueError, su.assert_mysql_db_uri, 'mysql://user:pass@server-no-db:3306/')

    def test_pass_assert_mysql_db_uri(self):
        su.assert_mysql_db_uri('mysql://user:pass@server:3306/db_name')

    def test_raises_assert_email(self):
        self.assertRaises(ValueError, su.assert_email, '')
        self.assertRaises(ValueError, su.assert_email, 'invalid_email.com')

    def test_passes_assert_email(self):
        su.assert_email('valid.email@domain.ac.uk')
