#!/usr/bin/env python
import logging
import requests
import argparse
import time
from server_utils import assert_http_uri
from requests.exceptions import HTTPError



def retry_requests(test_func):
    """
    Decorator for retrying calls to API in case of Network issues
    :param api_func: Api client function to call
    :return:
    """
    def retry_call_api(*args, **kwargs):
        retry = 1
        max_retry = 6
        while retry <= max_retry:
            try:
                return test_func(*args, **kwargs)
            except HTTPError as e:
                logging.warning('Call retry (%s/%s): ', retry, max_retry)
                retry += 1
                time.sleep(2)
                if retry > max_retry:
                    logging.error('API unrecoverable error after %s retry', retry-1)
                    raise e
    return retry_call_api
         
class RestClient(object):
    """
    Base client for interacting with a standard production REST service where the URIs meet a common standard.    
    Most methods are stubs for overriding or decoration by classes that extend this for specific services
    """
    
    jobs = '{}jobs'
    jobs_id = '{}jobs/{}'
    
    def __init__(self, uri):
        assert_http_uri(uri)
        self.uri = uri
    
    @retry_requests
    def submit_job(self, payload):
        """
        Submit a job using the supplied dict as payload. No checking is carried out on the payload
        Arguments:
          payload : job input as dict
        """
        logging.info("Submitting job")        
        logging.debug(payload)
        r = requests.post(self.jobs.format(self.uri), json=payload)
        r.raise_for_status()
        return r.json()['job_id']
    
    @retry_requests
    def delete_job(self, job_id, kill=False):
        """
        Delete job
        Arguments:
          job_id - ID of job to kill
          kill - if True, job process should be killed
        """
        delete_uri = self.jobs_id.format(self.uri, str(job_id))
        if kill:
            delete_uri += '?kill=1'
        r = requests.delete(delete_uri)
        r.raise_for_status()
        return True
    
    @retry_requests
    def list_jobs(self):
        """
        Find all current jobs
        """ 
        logging.info("Listing")
        r = requests.get(self.jobs.format(self.uri))
        r.raise_for_status()    
        return r.json()

    @retry_requests
    def retrieve_job_failure(self, job_id):
        """
        Retrieve information on a job using the special format "failure" which renders failures from the supplied job. 
        The service will respond if it supports this format.
        Arguments:
          job_id - ID of job to retrieve        
        """ 
        logging.info("Retrieving job failure for job " + str(job_id))
        r = requests.get(self.jobs_id.format(self.uri, str(job_id)) + '?format=failures')
        r.raise_for_status()
        failure_msg = r.json()
        return failure_msg

    @retry_requests
    def retrieve_job_email(self, job_id):
        """
        Retrieve information on a job using the special format "email" which renders the supplied job in a format suitable
        for sending by email. 
        The service will respond if it supports this format.
        Arguments:
          job_id - ID of job to retrieve        
        """ 
        logging.info("Retrieving job as email for job " + str(job_id))
        r = requests.get(self.jobs_id.format(self.uri, str(job_id)) + '?format=email')
        r.raise_for_status()
        return r.json()

    @retry_requests
    def retrieve_job(self, job_id):
        """
        Retrieve information on a job.
        Arguments:
          job_id - ID of job to retrieve        
        """
        logging.info("Retrieving results for job " + str(job_id))
        r = requests.get(self.jobs_id.format(self.uri, str(job_id)))
        r.raise_for_status()
        job = r.json()
        return job
    
    def print_job(self, job, print_results=False, print_input=False):
        """
        Stub utility to print job to logging 
        Arguments:
          job - job object
          print_results - ignored
          print_input - ignored
        """
        logging.info(job)
        
    def write_output(self, r, output_file):
        """
        Utility to write response. 
        Arguments:
          job - response object
          output_file - output file handle
        """                  
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
        logging.basicConfig(level=logging.DEBUG, format='%(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(message)s')
    
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
