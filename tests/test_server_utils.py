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
        self.assertTrue("memory_total_m" in status)
        self.assertTrue("memory_used_m" in status)
        self.assertTrue("memory_available_m" in status)
        self.assertTrue(status["memory_used_pct"]>=0)
        self.assertTrue(status["memory_used_pct"]<=100)

    def test_status_dir(self):
        status = get_status(dir_name="/")
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


        
