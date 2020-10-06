#!/usr/bin/env python

import logging
from urllib.parse import urlsplit, urlunsplit
import os
import requests
import argparse
import time
from ensembl_prodinf.server_utils import assert_http_uri
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


class RestClient(object):
    """
    Base client for interacting with a standard production REST service where the URIs meet a common standard.
    Most methods are stubs for overriding or decoration by classes that extend this for specific services
    """

    jobs = '{}jobs'
    jobs_id = '{}jobs/{}'
    src_host_list_url = 'src_host'
    tgt_host_list_url = 'tgt_host'


    def __init__(self, uri):
        assert_http_uri(uri)
        self.uri = uri
        self._http_adapter = self._make_HTTPAdapter()

    def _make_HTTPAdapter(self):
        retries = Retry(total=3, backoff_factor=1,
                        status_forcelist=[429, 500, 502, 503, 504],
                        method_whitelist=["GET", "PUT", "POST", "DELETE"])
        adapter = HTTPAdapter(max_retries=retries)
        return adapter

    def _session(self):
        http = requests.Session()
        http.mount("http://", self._http_adapter)
        return http

    def submit_job(self, payload):
        """
        Submit a job using the supplied dict as payload. No checking is carried out on the payload
        Arguments:
          payload : job input as dict
        """
        logging.info("Submitting job")
        logging.debug(payload)
        with self._session() as session:
            r = session.post(self.jobs.format(self.uri), json=payload)
        if r.status_code != 201:
            logging.error("failed to submit because: %s", r.text)
        r.raise_for_status()
        return r.json()['job_id']

    def delete_job(self, job_id, kill=False):
        """
        Delete job
        Arguments:
          job_id - ID of job to kill
          kill - if True, job process should be killed
        """
        delete_uri = self.jobs_id.format(self.uri, str(job_id))
        if kill:
            params = {'kill': '1'}
        else:
            params = {}
        with self._session() as session:
            r = session.delete(delete_uri, params=params)
        if r.status_code != 204:
            logging.error("failed to delete job because: %s", r.text)
        r.raise_for_status()
        return True

    def list_jobs(self):
        """
        Find all current jobs
        """
        logging.info("Listing")
        with self._session() as session:
            r = session.get(self.jobs.format(self.uri))
        if r.status_code != 200:
            logging.error("failed to list jobs because: %s", r.text)
        r.raise_for_status()
        return r.json()

    def retrieve_job_failure(self, job_id):
        """
        Retrieve information on a job using the special format "failure" which renders failures from the supplied job.
        The service will respond if it supports this format.
        Arguments:
          job_id - ID of job to retrieve
        """
        logging.info("Retrieving job failure for job %s", job_id)
        with self._session() as session:
            r = session.get(self.jobs_id.format(self.uri, str(job_id)), params={'format': 'failures'})
        if r.status_code != 200:
            logging.error("failed to retrieve job failures because: %s", r.text)
        r.raise_for_status()
        failure_msg = r.json()
        return failure_msg

    def retrieve_job_email(self, job_id):
        """
        Retrieve information on a job using the special format "email" which renders the supplied job in a format suitable
        for sending by email.
        The service will respond if it supports this format.
        Arguments:
          job_id - ID of job to retrieve
        """
        logging.info("Retrieving job as email for job %s", job_id)
        with self._session() as session:
            r = session.get(self.jobs_id.format(self.uri, str(job_id)), params={'format': 'email'})
        r.raise_for_status()
        return r.json()

    def retrieve_job(self, job_id):
        """
        Retrieve information on a job.
        Arguments:
          job_id - ID of job to retrieve
        """
        logging.info("Retrieving results for job %s", job_id)
        with self._session() as session:
            r = session.get(self.jobs_id.format(self.uri, str(job_id)))
        if r.status_code != 200:
            logging.error("failed to retrieve job because: %s", r.text)
        r.raise_for_status()
        job = r.json()
        return job

    def print_job(self, job, **kwargs):
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
        if output_file is not None:
            with output_file as f:
                f.write(r.text)

    def retrieve_host_list(self, host_type):
        if host_type == 'source':
            url = self.src_host_list_url
        elif host_type == 'target':
            url = self.tgt_host_list_url
        else:
            raise ValueError('Invalid host_type: %s. Use "source" or "target"' % host_type)
        # Deconstruct the url in order to work with new endpoints.
        # TODO: Refactor when the old db_copy service is retired.
        uri = urlsplit(self.uri)
        endpoint = urlunsplit((uri.scheme,
                               uri.netloc,
                               os.path.join(os.path.dirname(uri.path), url),
                               uri.query,
                               uri.fragment))
        with self._session() as session:
            r = session.get(endpoint)
        if r.status_code != 200:
            logging.error("Failed to retrieve host list: %s", r.text)
        r.raise_for_status()
        return r.json()


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

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format='%(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(message)s')

    if not args.uri.endswith('/'):
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
        logging.error("Unknown action %s", args.action)
