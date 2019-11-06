from ensembl_prodinf.hive import HiveInstance

from shutil import copy2
import unittest
import os 
import logging

dirpath = os.path.dirname(os.path.abspath(__file__))

logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

class HiveTest(unittest.TestCase):

    """Create fresh database file"""
    def setUp(self):
        logging.info("Creating test sqlite database")
        copy2(dirpath+"/test_pipeline.db.template",dirpath+"/test_pipeline.db")
        logging.info("Connecting to hive test sqlite database "+dirpath+"/test_pipeline.db")
        self.hive = HiveInstance("sqlite:///"+dirpath+"/test_pipeline.db")
        
    """Basic test case for creating a new job"""
    def test_create_job(self):
        job1 = self.hive.create_job('TestRunnable',{'x':'y','a':'b'})
        logging.debug(job1)
        job2 = self.hive.get_job_by_id(job1.job_id)
        logging.debug(job2)
        self.assertEquals(job1.job_id,job2.job_id)
        self.assertEquals(job1.analysis.logic_name,job2.analysis.logic_name)
        self.assertEquals(job1.input_id,job2.input_id)

    """Test case for checking on a finished semaphore"""
    def test_check_semaphore_success(self):  
        job = self.hive.get_job_by_id(2)
        logging.debug(job)
        status = self.hive.check_semaphores_for_job(job)
        logging.debug("Status for 2 is "+status)
        self.assertEquals(status, 'complete', "Checking expected status for completed semaphore")

    """Test case for checking on a failed semaphore"""
    def test_check_semaphore_failure(self):  
        job = self.hive.get_job_by_id(8)
        logging.debug(job)
        status = self.hive.check_semaphores_for_job(job)
        logging.debug("Status for 8 is "+status)
        self.assertEquals(status, 'failed', "Checking expected status for failed semaphore")

    """Test case for checking on a completed single job"""
    def test_check_job_success(self):
        job = self.hive.get_job_by_id(20)
        logging.debug(job)
        status = self.hive.get_job_tree_status(job)
        self.assertEquals("complete",status,"Checking status of completed single job")

    """Test case for checking on a failed single job"""
    def test_check_job_failure(self):
        job = self.hive.get_job_by_id(11)
        logging.debug(job)
        status = self.hive.get_job_tree_status(job)
        self.assertEquals("failed",status,"Checking status of failed single job")

    """Test case for checking on a completed job factory"""
    def test_check_job_tree_success(self):
        job = self.hive.get_job_by_id(1)
        logging.debug(job)
        status = self.hive.get_job_tree_status(job)
        logging.debug(status)
        self.assertEquals("complete",status,"Checking status of completed job factory")

    """Test case for checking on a failed job factory"""
    def test_check_job_tree_failure(self):
        job = self.hive.get_job_by_id(7)
        logging.debug(job)
        status = self.hive.get_job_tree_status(job)
        logging.debug(status)
        self.assertEquals("failed",status,"Checking status of failed job factory")

    """Test case for getting output on a completed job factory"""
    def test_get_job_output_success(self):
        output = self.hive.get_result_for_job_id(1)
        logging.debug(output)
        self.assertEquals('complete',output['status'],"Checking status of successful job factory output")
        self.assertTrue(output['output'] != None,"Checking output of successful job factory output")

    """Test case for getting output a failed job factory"""
    def test_get_job_output_failed(self):
        output = self.hive.get_result_for_job_id(7)
        logging.debug(output)
        self.assertEquals('failed', output['status'], "Checking status of unsuccessful job factory output")
        self.assertTrue('output' not in output, "Checking output of unsuccessful job factory output")

    """Test case for listing all jobs"""
    def test_get_all_results(self):
        jobs = self.hive.get_all_results('TestRunnable')
        self.assertEquals(1, len(jobs), "Checking we got just one job")
 
    """Remove test database file"""
    def tearDown(self):
        logging.info("Removing test sqlite database")
        #os.remove(dirpath+"/test_pipeline.db")

if __name__ == '__main__':
    unittest.main()
