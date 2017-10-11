#!/usr/bin/env python
import argparse
import logging
import requests

def write_output(r, output_file):
    if(output_file != None):
        with output_file as f:
            f.write(r.text)  
    
def submit_job(uri, source_db_uri, target_db_uri, only_tables, skip_tables, update, drop):
    logging.info("Submitting job")
    payload = {
        'source_db_uri':source_db_uri,
        'target_db_uri':target_db_uri,
        'only_tables':only_tables,
        'skip_tables':skip_tables,
        'update':update,
        'drop':drop,
        }
    logging.debug(payload)
    r = requests.post(uri+'submit', json=payload)
    r.raise_for_status()
    return r.json()['job_id']
    
def delete_job(uri, job_id):
    logging.info("Deleting job " + str(job_id))
    r = requests.get(uri + 'delete/' + job_id)
    r.raise_for_status()
    return True
    
def list_jobs(uri, output_file):
    logging.info("Listing")
    r = requests.get(uri + 'jobs')
    r.raise_for_status()
    return r.json()

    for job in r.json():
        print_job(uri, job, print_results=False, print_input=False)
    write_output(r, output_file)      
            
def retrieve_job(uri, job_id, output_file):    
    logging.info("Retrieving results for job " + str(job_id))
    r = requests.get(uri + 'results/' + job_id)
    r.raise_for_status()
    job = r.json()
    return job

def retrieve_job_failure(uri, job_id):    
    logging.info("Retrieving job failure for job " + str(job_id))
    r = requests.get(uri + 'failure/' + str(job_id))
    r.raise_for_status()
    failure_msg = r.json()
    return failure_msg
    
def print_job(uri, job, print_results=False, print_input=False):
    logging.info("Job %s (%s) to (%s) - %s" % (job['id'], job['input']['source_db_uri'], job['input']['target_db_uri'], job['status']))
    if print_input == True:
        print_inputs(job['input'])
    if print_results == True and job['status'] == 'complete':
        logging.info("Copy result: " + str(job['status']))
        logging.info("Copy took: " +str(job['output']['runtime']))
    elif job['status'] == 'failed':
      failure_msg = retrieve_job_failure(uri, job['id'])
      logging.info("Job failed with error: "+ str(failure_msg['msg']))

def print_inputs(i):
    logging.info("Source URI: " + i['source_db_uri'])
    logging.info("Target URI: " + i['target_db_uri'])
    if 'only_tables' in i:
      logging.info("List of tables to copy: " + i['only_tables'])
    elif 'skip_tables' in i:
      logging.info("List of tables to skip: " + i['skip_tables'])
    elif 'update' in i:
      logging.info("Incremental database update using rsync checksum set to: " + i['update'])
    elif 'drop' in i:
      logging.info("Drop database on Target server before copy set to: " + i['drop'])

if __name__ == '__main__':
            
    parser = argparse.ArgumentParser(description='Copy HCs via a REST service')

    parser.add_argument('-u', '--uri', help='REST service URI', required=True)
    parser.add_argument('-a', '--action', help='Action to take', choices=['submit', 'retrieve', 'list', 'delete'], required=True)
    parser.add_argument('-i', '--job_id', help='HC job identifier to retrieve')
    parser.add_argument('-v', '--verbose', help='Verbose output', action='store_true')
    parser.add_argument('-o', '--output_file', help='File to write output as JSON', type=argparse.FileType('w'))
    parser.add_argument('-s', '--source_db_uri', help='URI of database to copy from')
    parser.add_argument('-t', '--target_db_uri', help='URI of database to copy to')
    parser.add_argument('-y', '--only_tables', help='List of tables to copy')
    parser.add_argument('-n', '--skip_tables', help='List of tables to skip')
    parser.add_argument('-p', '--update', help='Incremental database update using rsync checksum')
    parser.add_argument('-d', '--drop', help='Drop database on Target server before copy')


    args = parser.parse_args()
    
    if args.verbose == True:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s - %(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s - %(message)s')
    
    if args.uri.endswith('/') == False:
        args.uri = args.uri + '/'    
            
    if args.action == 'submit':

        id = submit_job(args.uri, args.source_db_uri, args.target_db_uri, args.only_tables, args.skip_tables, args.update, args.drop)
        logging.info('Job submitted with ID '+str(id))
    
    elif args.action == 'retrieve':
    
        job = retrieve_job(args.uri, args.job_id, args.output_file)
        print_job(args.uri, job, print_input=True, print_results=True)
    
    elif args.action == 'list':
       
        jobs = list_jobs(args.uri, args.output_file)   
        for job in jobs:
            print_job(args.uri, job)
    
    elif args.action == 'delete':
        delete_job(args.uri, args.job_id)
        logging.info("Job " + str(args.job_id) + " was successfully deleted")
        
