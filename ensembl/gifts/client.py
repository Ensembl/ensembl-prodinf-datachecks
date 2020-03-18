#!/usr/bin/env python
import argparse
import logging
import json
import re
from collections import defaultdict
from ensembl.rest_client import RestClient
from ensembl.server_utils import assert_mysql_uri, assert_mysql_db_uri


class GIFTsClient(RestClient):
  """Client for interacting with the GIFTs services"""

  def submit_job(self, email, environment, tag, ensembl_release):
    """
    Start a GIFTs pipeline.
    Arguments:
      ensembl_release - mandatory Ensembl release number
      environment - mandatory execution environment (dev or staging)
      email - mandatory address for an email on job completion
      tag - optional text for annotating a submission
    """

    payload = {
      'ensembl_release': ensembl_release,
      'environment': environment,
      'email': email,
      'tag': tag
    }

    return RestClient.submit_job(self, payload)

  def list_jobs(self, output_file, pattern):
    """
    Find jobs and print results
    Arguments:
      output_file - optional file to write report
      pattern - optional pattern to filter jobs by
    """
    jobs = super(GIFTsClient, self).list_jobs()
    if pattern is None:
      pattern = '.*'
    tag_pattern = re.compile(pattern)
    output = []
    for job in jobs:
      if 'tag' in job['input']:
          tag = job['input']['tag']
      else:
          tag = ''
      if tag_pattern.search(tag):
        output.append(job)

    if output_file is None:
      print(json.dumps(output, indent=2))
    else:
      output_file.write(json.dumps(output))

  def print_job(self, job, print_results=False, print_input=False):
    """
    Render a job to logging
    Arguments:
      job :  job to print
      print_results : set to True to print detailed results
      print_input : set to True to print input for job
    """
    logging.info("Job %s - %s" % (job['id'], job['status']))
    if print_input == True:
      self.print_inputs(job['input'])
    if job['status'] == 'complete':
      if print_results == True:
        logging.info("Submission status: " + str(job['status']))
    elif job['status'] == 'incomplete':
      if print_results == True:
        logging.info("Submission status: " + str(job['status']))
    elif job['status'] == 'failed':
      logging.info("Submission status: " + str(job['status']))
      #failures = self.retrieve_job_failure(job['id'])
      #logging.info("Error: " + str(failures))
    else:
      raise ValueError("Unknown status {}".format(job['status']))

  def print_inputs(self, i):
    """Utility to render a job input dict to logging"""
    if 'ensembl_release' in i:
      logging.info("Ensembl Release: " + i['ensembl_release'])
    if 'environment' in i:
      logging.info("Environment: " + i['environment'])
    if 'email' in i:
      logging.info("Email: " + i['email'])
    if 'tag' in i:
      logging.info("Tag: " + i['tag'])


if __name__ == '__main__':

  parser = argparse.ArgumentParser(description='Ensembl Production: Interact with the GIFTs services')

  parser.add_argument('-u', '--uri', help='GIFTs Production service REST URI', required=True)
  parser.add_argument('-a', '--action', help='Action to take', choices=['submit', 'retrieve', 'list'], required=True)
  parser.add_argument('-i', '--job_id', help='GIFTs job identifier to retrieve')
  parser.add_argument('-v', '--verbose', help='Verbose output', action='store_true')
  parser.add_argument('-o', '--output_file', help='File to write output as JSON', type=argparse.FileType('w'))
  parser.add_argument('-r', '--ensembl_release', help='Ensembl release number', required=True)
  parser.add_argument('-n', '--environment', help='Execution environment (dev or staging)', required=True)
  parser.add_argument('-e', '--email', help='Email address for pipeline reports', required=True)
  parser.add_argument('-t', '--tag', help='Tag for annotating/retrieving a submission')

  args = parser.parse_args()

  if args.verbose == True:
    logging.basicConfig(level=logging.DEBUG, format='%(message)s')
  else:
    logging.basicConfig(level=logging.INFO, format='%(message)s')

  if args.uri.endswith('/') == False:
    args.uri = args.uri + '/'

  client = GIFTsClient(args.uri)

  if args.action == 'submit':
    job_id = client.submit_job(args.ensembl_release, args.environment, args.email, args.tag)
    logging.info('Job submitted with ID ' + str(job_id))

  elif args.action == 'retrieve':
    job = client.retrieve_job(args.job_id)
    client.print_job(job, print_results=True, print_input=True)

  elif args.action == 'list':
    jobs = client.list_jobs(args.output_file, args.tag)
