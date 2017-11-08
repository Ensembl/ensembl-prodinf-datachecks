#!/usr/bin/env python
import argparse
import logging
import requests
import json
import re
from collections import defaultdict

def submit_job(uri, db_uri, production_uri, compara_uri, staging_uri, live_uri, hc_names, hc_groups):
    logging.info("Submitting job")
    payload = {
        'db_uri':db_uri,
        'production_uri':production_uri,
        'compara_uri':compara_uri,
        'staging_uri':staging_uri,
        'live_uri':live_uri,
        'hc_names':hc_names,
        'hc_groups':hc_groups
        }
    logging.debug(payload)
    r = requests.post(uri+'submit', json=payload)
    r.raise_for_status()
    return r.json()['job_id']
    
def delete_job(uri, job_id):
    logging.info("Deleting job " + str(job_id))
    r = requests.get(uri + 'delete/' + str(job_id))
    r.raise_for_status()
    return True
    
def list_jobs(uri, output_file, pattern, failure_only):
    logging.info("Listing")
    r = requests.get(uri + 'jobs')
    r.raise_for_status()    
    output = []
    if pattern == None:
        pattern = '.*'
    re_pattern = re.compile(pattern)
    for job in r.json():
        if re_pattern.match(job['input']['db_uri']) and (failure_only == False or ('output' in job and job['output']['status'] == 'failed')):
            print_job(uri, job, print_results=False, print_input=False)
            if 'output' in job:
                if failure_only == True:
                    job['output']['results'] = {k: v for k, v in job['output']['results'].items() if v['status'] == 'failed'}
                output.append(job)
    if output_file!= None:
        output_file.write(json.dumps(output))

def collate_jobs(uri, output_file, pattern):
    logging.info("Collating jobs")
    r = requests.get(uri + 'jobs')
    r.raise_for_status()    
    if pattern == None:
        pattern = '.*'
    re_pattern = re.compile(pattern)
    output = defaultdict(list)
    for job in r.json():
        if re_pattern.match(job['input']['db_uri']) and ('output' in job and job['output']['status'] == 'failed'):
            for h,r in {k: v for k, v in job['output']['results'].iteritems() if v['status'] == 'failed'}.items():
                [output[h].append(job['input']['db_uri']+"\t"+m) for m in r['messages']]
    if output_file!= None:
        output_file.write(json.dumps(output))

def retrieve_job_failure(uri, job_id):
    logging.info("Retrieving job failure for job " + str(job_id))
    r = requests.get(uri + 'failures/' + str(job_id))
    r.raise_for_status()
    failure_msg = r.json()
    return failure_msg

def retrieve_job(uri, job_id, output_file):
    logging.info("Retrieving results for job " + str(job_id))
    r = requests.get(uri + 'results/' + str(job_id))
    r.raise_for_status()
    job = r.json()
    return job
    
def print_job(uri, job, print_results=False, print_input=False):
    logging.info("Job %s (%s) - %s" % (job['id'], job['input']['db_uri'], job['status']))
    if print_input == True:
        print_inputs(job['input'])
    if job['status'] == 'complete':
        if print_results == True:
            logging.info("HC result: " + str(job['output']['status']))
            for (hc, result) in job['output']['results'].iteritems():
                logging.info("%s : %s" % (hc, result['status']))
                if result['messages'] != None:
                    for msg in result['messages']:
                        logging.info(msg)
    elif job['status'] == 'failed':
        failures = retrieve_job_failure(uri, job['id'])
        logging.info("Job failed with error: "+ str(failures))

def print_inputs(i):
    logging.info("DB URI: " + i['db_uri'])
    logging.info("Staging URI: " + i['staging_uri'])
    logging.info("Live URI: " + i['live_uri'])
    logging.info("Compara URI: " + i['compara_uri'])
    logging.info("Production URI: " + i['production_uri'])
    if 'hc_names' in i:
        for hc in i['hc_names']:
            logging.info("HC: " + hc)
    if 'hc_groups' in i:
        for hc in i['hc_groups']:
            logging.info("HC: " + hc)

if __name__ == '__main__':
            
    parser = argparse.ArgumentParser(description='Run HCs via a REST service')

    parser.add_argument('-u', '--uri', help='HC REST service URI', required=True)
    parser.add_argument('-a', '--action', help='Action to take', choices=['submit', 'retrieve', 'list', 'delete', 'collate'], required=True)
    parser.add_argument('-i', '--job_id', help='HC job identifier to retrieve')
    parser.add_argument('-v', '--verbose', help='Verbose output', action='store_true')
    parser.add_argument('-o', '--output_file', help='File to write output as JSON', type=argparse.FileType('w'))
    parser.add_argument('-d', '--db_uri', help='URI of database to test')
    parser.add_argument('-p', '--production_uri', help='URI of production database')
    parser.add_argument('-c', '--compara_uri', help='URI of compara master database')
    parser.add_argument('-s', '--staging_uri', help='URI of current staging server')
    parser.add_argument('-l', '--live_uri', help='URI of live server for comparison')
    parser.add_argument('-n', '--hc_names', help='List of healthcheck names to run', nargs='*')
    parser.add_argument('-g', '--hc_groups', help='List of healthcheck groups to run', nargs='*')
    parser.add_argument('-r', '--db_pattern', help='Pattern of DB URIs to restrict by')
    parser.add_argument('-f', '--failure_only', help='Show failures only', action='store_true')

    args = parser.parse_args()
    
    if args.verbose == True:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s - %(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s - %(message)s')
    
    if args.uri.endswith('/') == False:
        args.uri = args.uri + '/'    
            
    if args.action == 'submit':

        id = submit_job(args.uri, args.db_uri, args.production_uri, args.compara_uri, args.staging_uri, args.live_uri, args.hc_names, args.hc_groups)
        logging.info('Job submitted with ID '+str(id))
    
    elif args.action == 'retrieve':
    
        job = retrieve_job(args.uri, args.job_id, args.output_file)
        print_job(args.uri, job, print_input=True, print_results=True)
    
    elif args.action == 'list':
       
        jobs = list_jobs(args.uri, args.output_file, args.db_pattern, args.failure_only)   

    elif args.action == 'collate':
       
        jobs = collate_jobs(args.uri, args.output_file, args.db_pattern)   
    
    elif args.action == 'delete':
        delete_job(args.uri, args.job_id)
        
