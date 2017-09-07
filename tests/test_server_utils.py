# -*- coding: utf-8 -*-

from ensembl_prodinf import get_status

import unittest
import logging

logging.basicConfig()

class ServerTest(unittest.TestCase):
    
    def test_status(self):
        status = get_status()
        logging.info(status)
        self.assertTrue("n_cpus" in status)
        self.assertTrue("load_1m" in status)
        self.assertTrue("load_5m" in status)
        self.assertTrue("load_15m" in status)
        self.assertTrue("memory_total" in status)
        self.assertTrue("memory_used" in status)
        self.assertTrue("memory_available" in status)

    def test_status_dir(self):
        status = get_status(dir_name="/")
        logging.info(status)
        self.assertTrue("n_cpus" in status)
        self.assertTrue("load_1m" in status)
        self.assertTrue("load_5m" in status)
        self.assertTrue("load_15m" in status)
        self.assertTrue("memory_total" in status)
        self.assertTrue("memory_used" in status)
        self.assertTrue("memory_available" in status)
        self.assertTrue("disk_total" in status)
        self.assertTrue("disk_used" in status)
        self.assertTrue("disk_available" in status)


    def test_status_host_dir(self):
        status = get_status(host="127.0.0.1", dir_name="/")
        logging.info(status)
        self.assertTrue("n_cpus" in status)
        self.assertTrue("load_1m" in status)
        self.assertTrue("load_5m" in status)
        self.assertTrue("load_15m" in status)
        self.assertTrue("memory_total" in status)
        self.assertTrue("memory_used" in status)
        self.assertTrue("memory_available" in status)
        self.assertTrue("disk_total" in status)
        self.assertTrue("disk_used" in status)
        self.assertTrue("disk_available" in status)
        
