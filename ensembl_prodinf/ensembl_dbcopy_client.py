#!/usr/bin/env python3

import argparse
import logging
import re
import sys
from ensembl_prodinf.rest_client import RestClient


class DbCopyRestClient(RestClient):
    """
    Client for submitting database copy jobs to the db copy REST API
    """

    jobs = '{}'
    jobs_id = '{}/{}'

    def submit_job(self, src_host, src_incl_db, src_skip_db, src_incl_tables,
                   src_skip_tables, tgt_host, tgt_db_name, tgt_directory,
                   skip_optimize, wipe_target, convert_innodb, email_list, user):
        """
        Submit a new job
        Arguments:
          src_host : Source host for the copy (host:port)
          src_incl_db : List of database to include in the copy. If not defined all the databases from the server will be copied
          src_skip_db : List of database to exclude from the copy.
          src_incl_tables : List of tables to include in the copy.
          src_skip_tables : List of tables to exclude from the copy.
          tgt_host : List of hosts to copy to (host:port,host:port)
          tgt_db_name : Name of database on target server. Used for renaming databases
          tgt_directory: Target directory path on the target machine
          skip_optimize : Skip the database optimization step after the copy. Useful for very large databases
          wipe_target: Delete database on target before copy
          convert_innodb: Convert innoDB tables to MyISAM
          email_list: List of emails
          user: user name
        """
        payload = {
            'src_host':src_host,
            'src_incl_db':src_incl_db,
            'src_skip_db':src_skip_db,
            'src_incl_tables':src_incl_tables,
            'src_skip_tables':src_skip_tables,
            'tgt_host':tgt_host,
            'tgt_db_name':tgt_db_name,
            'tgt_directory':tgt_directory,
            'skip_optimize':skip_optimize,
            'wipe_target':wipe_target,
            'convert_innodb':convert_innodb,
            'email_list':email_list,
            'user':user,
        }
        return super().submit_job(payload)

    def print_job(self, job, user, print_results=False):
        """
        Print out details of a job
        Arguments:
          job : Job to render
          print_results : set to True to show results
          user: name of the user to filter on
        """
        if 'url' in job:
            if user:
                if user == job['user']:
                    logging.info("Job %s from (%s) to (%s) by %s - status: %s",
                                 job['url'], job['src_host'], job['tgt_host'], job['user'], job['overall_status'])
            else:
                logging.info("Job %s from (%s) to (%s) by %s - status: %s",
                             job['url'], job['src_host'], job['tgt_host'], job['user'], job['overall_status'])
        else:
            if user:
                if user == job['user']:
                    logging.info("Job %s from (%s) to (%s) by %s - status: %s",
                                 job['job_id'], job['src_host'], job['tgt_host'], job['user'], job['overall_status'])
            else:
                logging.info("Job %s from (%s) to (%s) by %s - status: %s",
                             job['job_id'], job['src_host'], job['tgt_host'], job['user'], job['overall_status'])
        if job['overall_status'] == 'Running':
            if print_results == True:
                logging.info("Copy status: %s", job['overall_status'])
                logging.info("%s complete", job['detailed_status']['progress'])

    def print_inputs(self, i):
        """
        Print out details of job input
        Arguments:
          i : job input
        """
        logging.info("Source host: %s", i['src_host'])
        logging.info("Target hosts: %s", i['tgt_host'])
        logging.info("Detailed parameters:")
        logging.info("%s", i)

    def check_host(self, host_type, url):
        hosts = self.retrieve_host_list(host_type)['results']
        host_port_map = dict(list(map(lambda x: (x['name'], x['port']), hosts)))
        host, port = url.split(':')
        host_parts = host.split('.')
        if len(host_parts) > 1:
            if not host.endswith('.ebi.ac.uk'):
                return False, 'Invalid hostname: {}'.format(host)
        hostname = host_parts[0]
        actual_port = host_port_map.get(hostname)
        if actual_port is None:
            return False, 'Invalid hostname: {}'.format(host)
        if int(port) != int(actual_port):
            return False, 'Invalid port for hostname: {}. Please use port: {}'.format(host, actual_port)
        if int(port) == int(actual_port):
            return True, ''


def main():
    parser = argparse.ArgumentParser(description='Copy Databases via a REST service')

    parser.add_argument('-u', '--uri', help='Copy database REST service URI', required=True)
    parser.add_argument('-a', '--action', help='Action to take', choices=['submit', 'retrieve', 'list', 'delete', 'email', 'kill_job'], required=True)
    parser.add_argument('-j', '--job_id', help='Copy job identifier to retrieve')
    parser.add_argument('-v', '--verbose', help='Verbose output', action='store_true')
    parser.add_argument('-s', '--src_host', help='Source host for the copy')
    parser.add_argument('-t', '--tgt_host', help='Target hosts for the copy')
    parser.add_argument('-i', '--src_incl_db', help='List of tables to copy')
    parser.add_argument('-k', '--src_skip_db', help='List of tables to skip')
    parser.add_argument('-p', '--src_incl_tables', help='Incremental database update using rsync checksum')
    parser.add_argument('-d', '--src_skip_tables', help='Drop database on Target server before copy')
    parser.add_argument('-n', '--tgt_db_name', help='Convert InnoDB tables to MyISAM after copy')
    parser.add_argument('-g', '--tgt_directory', help='Skip the database optimization step after the copy. Useful for very large databases')
    parser.add_argument('-o', '--skip_optimize', help='Email where to send the report')
    parser.add_argument('-w', '--wipe_target', help='Delete target database before copy')
    parser.add_argument('-c', '--convert_innodb', help='Email where to send the report')
    parser.add_argument('-e', '--email_list', help='Email where to send the report')
    parser.add_argument('-r', '--user', help='User name')
    parser.add_argument('--skip-check', action='store_true', default=False, help='Skip host:port server validation')

    args = parser.parse_args()

    if args.verbose == True:
        logging.basicConfig(level=logging.DEBUG, format='%(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(message)s')

    client = DbCopyRestClient(args.uri)

    if args.skip_optimize == None:
        args.skip_optimize = 0
    if args.wipe_target == None:
        args.wipe_target = 0
    if args.convert_innodb == None:
        args.convert_innodb = 0

    if args.action == 'submit':
        logging.info('Submitting %s -> %s', args.src_host, args.tgt_host)
        if not args.skip_check:
            logging.info('Checking source and target hostname validity...')
            source_valid, source_msg = client.check_host('source', args.src_host)
            target_valid, target_msg = client.check_host('target', args.tgt_host)
            if not source_valid:
                logging.error('Source hostname error: %s', source_msg)
            if not target_valid:
                logging.error('Target hostname error: %s', target_msg)
            if not (source_valid and target_valid):
                sys.exit(1)
        job_id = client.submit_job(args.src_host, args.src_incl_db, args.src_skip_db, args.src_incl_tables,
                                   args.src_skip_tables, args.tgt_host, args.tgt_db_name, args.tgt_directory,
                                   args.skip_optimize, args.wipe_target, args.convert_innodb, args.email_list, args.user)
        logging.info('Job submitted with ID %s', job_id)

    elif args.action == 'retrieve':
        job = client.retrieve_job(args.job_id)
        client.print_job(job, args.user, print_results=True)

    elif args.action == 'list':
        jobs = client.list_jobs()
        for job in jobs:
            client.print_job(job, args.user)


if __name__ == '__main__':
    main()
