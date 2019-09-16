#!/usr/bin/env python
import argparse
import logging
import json
import re
from collections import defaultdict
from ensembl.rest_client import RestClient
from ensembl.server_utils import assert_mysql_uri, assert_mysql_db_uri


class DatacheckClient(RestClient):
  """Client for checking databases using the datacheck service"""

  def submit_job(self, server_url, database, species, division, db_type, release,
                 datacheck_names, datacheck_groups, datacheck_types,
                 config_profile, email, tag):
    """
    Run datachecks on a given server, for one or more species.
    Parameter requirements are complicated, because only the server_url is absolutely required,
    for lots of other parameters you need one from a set, but it doesn't matter which one...
    Arguments:
      server_url - location of server, in URI format
      database - name of a database to check
      species - name of a species to check
      division - name of a division to check
      db_type - type of database to check, defaults to 'core'
      release - release number of database to check, defaults to current development version

      datacheck_names - names of datacheck(s) to run, multiple values must be comma-separated
      datacheck_groups - datacheck group(s) to run, multiple values must be comma-separated
      datacheck_types - optional filter on type, 'critical' or 'advisory'

      config_profile - a division name, used to load appropriate parameters
      email - optional address for an email on job completion
      tag - optional text for grouping datacheck submissions
    """
    assert_mysql_uri(server_url)

    payload = {
      'server_url': server_url,
      'database': database,
      'species': None,
      'division': None,
      'db_type': db_type,
      'release': release,
      'datacheck_names': [],
      'datacheck_groups': [],
      'datacheck_types': [],
      'config_profile': config_profile,
      'email': email,
      'tag': tag
    }

    if species is not None:
      payload['species'] = species.split(',')
    elif division is not None:
      payload['division'] = division.split(',')

    if datacheck_names is not None:
      payload['datacheck_names'] = datacheck_names.split(',')
    if datacheck_groups is not None:
      payload['datacheck_groups'] = datacheck_groups.split(',')
    if datacheck_types is not None:
      payload['datacheck_types'] = datacheck_types.split(',')

    return RestClient.submit_job(self, payload)

  def list_jobs(self, output_file, pattern, failure_only=False):
    """
    Find jobs and print results
    Arguments:
      output_file - optional file to write report
      pattern - optional pattern to filter jobs by
      failure_only - only report failed jobs
    """
    jobs = super(DatacheckClient, self).list_jobs()
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
		  if 'output' in job:
			if failure_only == True:
				if job['output']['failed_total'] > 0:
					output.append(job)
			else:
				output.append(job)
		  else:
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
        logging.info("Database passed: " + str(job['output']['passed_total']))
        logging.info("Database failed: " + str(job['output']['failed_total']))
        logging.info("Output directory: " + str(job['output']['output_dir']))
        logging.info("Per database results: ")
        logging.info(json.dumps(job['output']['databases'], indent=2))
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
    logging.info("Registry file: " + i['registry_file'])
    if 'database' in i:
      logging.info("Database name: " + i['database'])
    if 'species' in i:
      for species in i['species']:
		logging.info("Species name: " + species)
    if 'division' in i:
      for division in i['division']:
		logging.info("Division name: " + division)
    if 'db_type' in i:
      logging.info("Database type: " + i['db_type'])
    if 'release' in i:
      logging.info("Ensembl release: " + i['release'])
    if 'datacheck_names' in i:
      for name in i['datacheck_names']:
        logging.info("Datacheck: " + name)
    if 'datacheck_groups' in i:
      for group in i['datacheck_groups']:
        logging.info("Datacheck group: " + group)
    if 'datacheck_types' in i:
      for datacheck_type in i['datacheck_types']:
		logging.info("Datacheck type: " + datacheck_type)
    if 'config_profile' in i:
      logging.info("Config profile: " + i['config_profile'])
    if 'email' in i:
      logging.info("Email: " + i['email'])
    if 'tag' in i:
      logging.info("Tag: " + i['tag'])


if __name__ == '__main__':

  parser = argparse.ArgumentParser(description='Run datachecks via a REST service')

  parser.add_argument('-u', '--uri', help='Datacheck REST service URI', required=True)
  parser.add_argument('-a', '--action', help='Action to take',
                      choices=['submit', 'retrieve', 'list'], required=True)
  parser.add_argument('-i', '--job_id', help='Datacheck job identifier to retrieve')
  parser.add_argument('-v', '--verbose', help='Verbose output', action='store_true')
  parser.add_argument('-o', '--output_file', help='File to write output as JSON', type=argparse.FileType('w'))
  parser.add_argument('-s', '--server_url', help='URL of database server', required=True)
  parser.add_argument('-db', '--database', help='Database name')
  parser.add_argument('-sp', '--species', help='Species production name')
  parser.add_argument('-div', '--division', help='Division')
  parser.add_argument('-dbt', '--db_type', help='Database type')
  parser.add_argument('-r', '--release', help='Ensembl release version')
  parser.add_argument('-n', '--datacheck_names', help='Datacheck names, multiple names comma-separated')
  parser.add_argument('-g', '--datacheck_groups', help='Datacheck groups, multiple names comma-separated')
  parser.add_argument('-dct', '--datacheck_types', help='Datacheck type (advisory or critical)')
  parser.add_argument('-c', '--config_profile', help='Division for configuration')
  parser.add_argument('-e', '--email', help='Email address for pipeline reports')
  parser.add_argument('-t', '--tag', help='Tag to collate results and facilitate filtering')
  parser.add_argument('-f', '--failure_only', help='Show failures only', action='store_true')

  args = parser.parse_args()

  if args.verbose == True:
    logging.basicConfig(level=logging.DEBUG, format='%(message)s')
  else:
    logging.basicConfig(level=logging.INFO, format='%(message)s')

  if args.uri.endswith('/') == False:
    args.uri = args.uri + '/'

  client = DatacheckClient(args.uri)

  if args.action == 'submit':
    job_id = client.submit_job(args.server_url, args.database, args.species, args.division, args.db_type, args.release,
                               args.datacheck_names, args.datacheck_groups, args.datacheck_types,
                               args.config_profile, args.email, args.tag)
    logging.info('Job submitted with ID ' + str(job_id))

  elif args.action == 'retrieve':
    job = client.retrieve_job(args.job_id)
    client.print_job(job, print_results=True, print_input=True)

  elif args.action == 'list':
    jobs = client.list_jobs(args.output_file, args.tag, args.failure_only)

