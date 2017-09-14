#!/usr/bin/env python
import argparse
import logging
import requests

def write_output(r, output_file):
    if(output_file != None):
        with output_file as f:
            f.write(r.text)  
    
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
    r = requests.get(uri + 'delete/' + job_id)
    r.raise_for_status()
    return True
    
def list_jobs(uri, output_file):
    logging.info("Listing")
    r = requests.get(uri + 'jobs')
    r.raise_for_status()
    return r.json()

    for job in r.json():
        print_job(job, print_results=False, print_input=False)
    write_output(r, output_file)      
            
def retrieve_job(uri, job_id, output_file):    
    logging.info("Retrieving results for job " + str(job_id))
    r = requests.get(uri + 'results/' + job_id)
    r.raise_for_status()
    job = r.json()
    return job
    
def print_job(job, print_results=False, print_input=False):
    logging.info("Job %s (%s) - %s" % (job['id'], job['input']['db_uri'], job['status']))
    if print_input == True:
        print_inputs(job['input'])
    if print_results == True and job['status'] == 'complete':
        logging.info("HC result: " + str(job['output']['status']))
        for (hc, result) in job['output']['results'].iteritems():
            logging.info("%s : %s" % (hc, result['status']))
            if result['messages'] != None:
                for msg in result['messages']:
                    logging.info(msg)

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
    parser.add_argument('-a', '--action', help='Action to take', choices=['submit', 'retrieve', 'list', 'delete'], required=True)
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
        print_job(job, print_input=True, print_result=True)
    
    elif args.action == 'list':
       
        jobs = list_jobs(args.uri, args.output_file)   
        for job in jobs:
            print_job(job)
    
    elif args.action == 'delete':
        delete_job(args.uri, args.job_id)
        
