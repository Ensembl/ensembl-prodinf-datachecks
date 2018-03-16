#!/usr/bin/env python
import logging
import requests
import argparse   
from server_utils import assert_http_uri
         
class RestClient(object):
    
    jobs = '{}jobs'
    jobs_id = '{}jobs/{}'
    
    def __init__(self, uri):
        assert_http_uri(uri)
        self.uri = uri
    
    def submit_job(self, payload):
        logging.info("Submitting job")        
        logging.debug(payload)
        r = requests.post(self.jobs.format(self.uri), json=payload)
        r.raise_for_status()
        return r.json()['job_id']
    
    def delete_job(self, job_id):
        r = requests.delete(self.jobs_id.format(self.uri, str(job_id)))
        r.raise_for_status()
        return True
    
    def list_jobs(self):
        logging.info("Listing")
        r = requests.get(self.jobs.format(self.uri))
        r.raise_for_status()    
        return r.json()

    def retrieve_job_failure(self, job_id):
        logging.info("Retrieving job failure for job " + str(job_id))
        r = requests.get(self.jobs_id.format(self.uri, str(job_id)) + '?format=failures')
        r.raise_for_status()
        failure_msg = r.json()
        return failure_msg

    def retrieve_job(self, job_id):
        logging.info("Retrieving results for job " + str(job_id))
        r = requests.get(self.jobs_id.format(self.uri, str(job_id)))
        r.raise_for_status()
        job = r.json()
        return job
    
    def print_job(self, job, print_results=False, print_input=False):
        logging.info(job)
        
    def write_output(self, r, output_file):
        if(output_file != None):
            with output_file as f:
                f.write(r.text)  
    
    
if __name__ == '__main__':
            
    parser = argparse.ArgumentParser(description='Run HCs via a REST service')

    parser.add_argument('-u', '--uri', help='HC REST service URI', required=True)
    parser.add_argument('-a', '--action', help='Action to take', choices=['submit', 'retrieve', 'list', 'delete', 'collate'], required=True)
    parser.add_argument('-i', '--job_id', help='HC job identifier to retrieve')
    parser.add_argument('-v', '--verbose', help='Verbose output', action='store_true')
    parser.add_argument('-o', '--output_file', help='File to write output as JSON', type=argparse.FileType('w'))
    parser.add_argument('-f', '--failure_only', help='Show failures only', action='store_true')
    parser.add_argument('-e', '--email', help='User email')

    args = parser.parse_args()
    
    if args.verbose == True:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s - %(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s - %(message)s')
    
    if args.uri.endswith('/') == False:
        args.uri = args.uri + '/'   
        
    client = RestClient(args.uri)
                
    if args.action == 'retrieve':
        job = client.retrieve_job(args.job_id)
        client.print_job(job, print_results=True, print_input=True)
    
    elif args.action == 'list':
        jobs = client.list_jobs()   

    elif args.action == 'delete':
        client.delete_job(args.job_id)
    
    else:
        logging.error("Unknown action {}".format(args.action))