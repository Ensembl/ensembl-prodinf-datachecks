from shutil import copy2
import unittest
import hc_app
import os 
import logging
import json

dirpath = os.path.dirname(os.path.abspath(__file__))

logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

class HcSrvTest(unittest.TestCase):
    
    """Create fresh database file"""
    def setUp(self):
        logging.info("Creating test sqlite database")
        copy2(dirpath+"/test_hc.db.single",dirpath+"/test_hc.db")
        logging.info("Connecting to hive test sqlite database "+dirpath+"/test_hc.db")
        hc_app.app.config['HIVE_URI'] = "sqlite:///"+dirpath+"/test_hc.db"
        print hc_app
        hc_app.app.testing = True
        self.app = hc_app.app.test_client()

        
    """Basic test case for creating a new job"""
    def test_submit(self):
        input = {
            'db_uri':'banana',
            'hc_names': ['apple','mango']
        }
        response=self.app.post('/submit', 
                               data=json.dumps(input),
                               content_type='application/json')
        self.assertEquals(200, response.status_code)
        results = json.loads(response.data)
        self.assertTrue(results.get('job_id'))
        response2 = self.app.get("/results/"+str(results.get('job_id')));
        self.assertEquals(200, response2.status_code)
        results2 = json.loads(response2.data);
        print results2
        self.assertEquals(results2.get('id'),results.get('job_id'))
        self.assertEquals(results2.get('status'),'incomplete')        


    """Basic test case for retrieving job as json"""
    def test_results(self):
        response = self.app.get("/results/1");
        self.assertEquals(200, response.status_code)
        results = json.loads(response.data);
        print results
        self.assertEquals(results.get('id'),1)
        self.assertEquals(results.get('status'),'complete')
        output = results.get('output')
        self.assertEquals(output.get('status'),'failure')
        self.assertEquals(output.get('db_name'),'homo_sapiens_core_90_38')

    """Basic test case for retrieving job as email"""
    def test_results_email(self):
        response = self.app.get("/results_email/1");
        self.assertEquals(200, response.status_code)
        results = json.loads(response.data);
        print results
        self.assertEquals(results.get('status'),'complete')
        self.assertTrue(results.get('body'))
        self.assertTrue(results.get('subject'))

    """Remove test database file"""
    def tearDown(self):
        logging.info("Removing test sqlite database")
        os.remove(dirpath+"/test_hc.db")

if __name__ == '__main__':
    unittest.main()
