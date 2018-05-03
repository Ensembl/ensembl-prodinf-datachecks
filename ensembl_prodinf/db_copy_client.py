#!/usr/bin/env python
import argparse
import logging
import re
from rest_client import RestClient
from server_utils import assert_mysql_db_uri

class DbCopyClient(RestClient):
    
    """
    Client for submitting database copy jobs to the db copy REST API
    """

    def submit_job(self, source_db_uri, target_db_uri, only_tables, skip_tables, update, drop, email):
        """
        Submit a new job
        Arguments:
          source_db_uri : URI of MySQL schema to copy from
          target_db_uri : URI of MySQL schema to copy to 
          only_tables : list of tables to copy (others are skipped)
          skip_tables : list of tables to skip from the copy
          update : set to True to run an incremental update
          drop : set to True to drop the schema first
          email : optional address for job completion email
        """
        assert_mysql_db_uri(source_db_uri)
        assert_mysql_db_uri(target_db_uri)
        
        if only_tables:
            if (not re.search(r"^([^ ]+){1}$", only_tables) or not re.search(r"^([^ ]+){1}(,){1}([^ ]+){1}$", only_tables)):
                raise ValueError("List of tables need to be comma separated, eg: table1,table2,table3")
        if skip_tables:
            if (not re.search(r"^([^ ]+){1}$", skip_tables) or not re.search(r"^([^ ]+){1}(,){1}([^ ]+){1}$", skip_tables)):
                raise ValueError("List of tables need to be comma separated, eg: table1,table2,table3")
    
        logging.info("Submitting job")
        payload = {
            'source_db_uri':source_db_uri,
            'target_db_uri':target_db_uri,
            'only_tables':only_tables,
            'skip_tables':skip_tables,
            'update':update,
            'drop':drop,
            'email':email
        }
        return super(DbCopyClient, self).submit_job(payload)

    def kill_job(self, job_id):
        """
        Kill a running job
        Arguments:
          job_id : Job to kill
        """
        return super(DbCopyClient, self).kill_job(job_id, 1)
    
    def print_job(self, job, print_results=False, print_input=False):
        """
        Print out details of a job
        Arguments:
          job : Job to render
          print_results : set to True to show results
          print_input : set to True to show input
        """
        logging.info("Job %s (%s) to (%s) - %s" % (job['id'], job['input']['source_db_uri'], job['input']['target_db_uri'], job['status']))
        if print_input == True:
            self.print_inputs(job['input'])
        if job['status'] == 'complete':
            if print_results == True:
                logging.info("Copy result: " + str(job['status']))
                logging.info("Copy took: " +str(job['output']['runtime']))
        elif job['status'] == 'running':
            if print_results == True:
                logging.info("HC result: " + str(job['status']))
                logging.info(str(job['progress']['complete'])+"/"+str(job['progress']['total'])+" task complete")
                logging.info("Status: "+str(job['progress']['message']))
        elif job['status'] == 'failed':
            failure_msg = self.retrieve_job_failure(job['id'])
            logging.info("Job failed with error: "+ str(failure_msg['msg']))

    def print_inputs(self, i):
        
        """
        Print out details of job input
        Arguments:
          i : job input
        """
        
        logging.info("Source URI: " + i['source_db_uri'])
        logging.info("Target URI: " + i['target_db_uri'])
        if 'only_tables' in i:
            logging.info("List of tables to copy: " + i['only_tables'])
        if 'skip_tables' in i:
            logging.info("List of tables to skip: " + i['skip_tables'])
        if 'update' in i:
            logging.info("Incremental database update using rsync checksum set to: " + i['update'])
        if 'drop' in i:
            logging.info("Drop database on Target server before copy set to: " + i['drop'])
        if 'email' in i:
            logging.info("email: " + i['email'])

if __name__ == '__main__':
            
    parser = argparse.ArgumentParser(description='Copy Databases via a REST service')

    parser.add_argument('-u', '--uri', help='Copy database REST service URI', required=True)
    parser.add_argument('-a', '--action', help='Action to take', choices=['submit', 'retrieve', 'list', 'delete', 'email', 'kill_job'], required=True)
    parser.add_argument('-i', '--job_id', help='HC job identifier to retrieve')
    parser.add_argument('-v', '--verbose', help='Verbose output', action='store_true')
    parser.add_argument('-o', '--output_file', help='File to write output as JSON', type=argparse.FileType('w'))
    parser.add_argument('-f', '--input_file', help='File containing list of source and target URIs', type=argparse.FileType('r'))
    parser.add_argument('-s', '--source_db_uri', help='URI of database to copy from')
    parser.add_argument('-t', '--target_db_uri', help='URI of database to copy to')
    parser.add_argument('-y', '--only_tables', help='List of tables to copy')
    parser.add_argument('-n', '--skip_tables', help='List of tables to skip')
    parser.add_argument('-p', '--update', help='Incremental database update using rsync checksum')
    parser.add_argument('-d', '--drop', help='Drop database on Target server before copy')
    parser.add_argument('-e', '--email', help='Email where to send the report')


    args = parser.parse_args()
    
    if args.verbose == True:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s - %(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s - %(message)s')
    
    if args.uri.endswith('/') == False:
        args.uri = args.uri + '/'    
    
    client = DbCopyClient(args.uri)
            
    if args.action == 'submit':

        if args.input_file == None:
            logging.info("Submitting " + args.source_db_uri + "->" + args.target_db_uri)
            job_id = client.submit_job(args.source_db_uri, args.target_db_uri, args.only_tables, args.skip_tables, args.update, args.drop, args.email)
            logging.info('Job submitted with ID '+str(job_id))
        else:
            for line in args.input_file:
                uris = line.split()
                logging.info("Submitting " + uris[0] + "->" + uris[1])
                job_id = client.submit_job(uris[0], uris[1], args.only_tables, args.skip_tables, args.update, args.drop, args.email)
                logging.info('Job submitted with ID '+str(job_id))
    
    elif args.action == 'retrieve':
    
        job = client.retrieve_job(args.job_id)
        client.print_job(job, print_results=True, print_input=True)
    
    elif args.action == 'list':
       
        jobs = client.list_jobs()   
        for job in jobs:
            client.print_job(job)
    
    elif args.action == 'delete':
        client.delete_job(args.job_id)
        logging.info("Job " + str(args.job_id) + " was successfully deleted")

    elif args.action == 'email':
        client.job_email(args.job_id, args.email)

    elif args.action == 'kill_job':
        client.kill_job(args.job_id)
        
