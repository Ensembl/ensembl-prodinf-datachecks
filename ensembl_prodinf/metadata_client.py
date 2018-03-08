#!/usr/bin/env python
import argparse
import logging
import requests
import sys
import re

def write_output(r, output_file):
    if(output_file != None):
        with output_file as f:
            f.write(r.text)  
    
def submit_job(uri, metadata_uri, database_uri, e_release, eg_release, release_date, current_release, email, update_type, comment, source):
    db_uri_regex = r"^(mysql://){1}(.+){1}(:.+){0,1}(@){1}(.+){1}(:){1}(\d+){1}(/){1}(.+){1}$"
    http_uri_regex = r"^(http){1}(s){0,1}(://){1}(.+){1}(:){1}(\d+){1}(/){1}(.+){0,1}$"
    if not re.search(http_uri_regex, uri):
        sys.exit("DB endpoint URL don't match pattern: http://server_name:port/")
    if not re.search(db_uri_regex, metadata_uri):
        sys.exit("Database URI don't match pattern: mysql://user(:pass)@server:port/")
    if not re.search(db_uri_regex, database_uri):
        sys.exit("Database URI don't match pattern: mysql://user(:pass)@server:port/")
    logging.info("Submitting job")
    payload = {
        'metadata_uri':metadata_uri,
        'database_uri':database_uri,
        'e_release':e_release,
        'eg_release':eg_release,
        'release_date':release_date,
        'current_release':current_release,
        'email':email,
        'update_type':update_type,
        'comment':comment,
        'source':source,
        }
    logging.debug(payload)
    r = requests.post(uri+'submit', json=payload)
    r.raise_for_status()
    return r.json()['job_id']
    
def delete_job(uri, job_id):
    uri_regex = r"^(http){1}(s){0,1}(://){1}(.+){1}(:){1}(\d+){1}(/){1}(.+){0,1}$"
    if not re.search(uri_regex, uri):
        sys.exit("DB endpoint URL don't match pattern: http://server_name:port/")
    if not re.search(r"\d+", job_id):
        sys.exit("job_id should be a number")
    logging.info("Deleting job " + str(job_id))
    r = requests.get(uri + 'delete/' + job_id)
    r.raise_for_status()
    return True
    
def list_jobs(uri, output_file):
    uri_regex = r"^(http){1}(s){0,1}(://){1}(.+){1}(:){1}(\d+){1}(/){1}(.+){0,1}$"
    if not re.search(uri_regex, uri):
        sys.exit("DB endpoint URL don't match pattern: http://server_name:port/")
    logging.info("Listing")
    r = requests.get(uri + 'jobs')
    r.raise_for_status()
    return r.json()

    for job in r.json():
        print_job(uri, job, print_results=False, print_input=False)
    write_output(r, output_file)      
            
def retrieve_job(uri, job_id, output_file):    
    uri_regex = r"^(http){1}(s){0,1}(://){1}(.+){1}(:){1}(\d+){1}(/){1}(.+){0,1}(.+){0,1}$"
    if not re.search(uri_regex, uri):
        sys.exit("DB endpoint URL don't match pattern: http://server_name:port/")
    if not re.search(r"\d+", job_id):
        sys.exit("job_id should be a number")
    logging.info("Retrieving results for job " + str(job_id))
    r = requests.get(uri + 'results/' + job_id)
    r.raise_for_status()
    job = r.json()
    return job

def results_email(uri, job_id, email):
    uri_regex = r"^(http){1}(s){0,1}(://){1}(.+){1}(:){1}(\d+){1}(/){1}(.+){0,1}$"
    if not re.search(uri_regex, uri):
        sys.exit("DB endpoint URL don't match pattern: http://server_name:port/")
    if not re.search(r"\d+", job_id):
        sys.exit("job_id should be a number")
    if not re.search(r"^(.+){1}(@){1}(.+){1}$", email):
        sys.exit("email should match pattern john.doe@ebi.ac.uk")
    logging.info("Sending job detail by email " + str(job_id))
    r = requests.get(uri + 'results_email/' + str(job_id) + "?email=" + str(email))
    r.raise_for_status()
    return r.json()

def retrieve_job_failure(uri, job_id):    
    uri_regex = r"^(http){1}(s){0,1}(://){1}(.+){1}(:){1}(\d+){1}(/){1}(.+){0,1}$"
    if not re.search(uri_regex, uri):
        sys.exit("DB endpoint URL don't match pattern: http://server_name:port/")
    if not re.search(r"\d+", job_id):
        sys.exit("job_id should be a number")
    logging.info("Retrieving job failure for job " + str(job_id))
    r = requests.get(uri + 'failure/' + str(job_id))
    r.raise_for_status()
    failure_msg = r.json()
    return failure_msg
    
def print_job(uri, job, print_results=False, print_input=False):
    uri_regex = r"^(http){1}(s){0,1}(://){1}(.+){1}(:){1}(\d+){1}(/){1}(.+){0,1}$"
    if not re.search(uri_regex, uri):
        sys.exit("DB endpoint URL don't match pattern: http://server_name:port/")
    logging.info("Job %s (%s) to (%s) - %s" % (job['id'], job['input']['metadata_uri'], job['input']['database_uri'], job['status']))
    if print_input == True:
        print_inputs(job['input'])
    if job['status'] == 'complete':
        if print_results == True:
            logging.info("Load result: " + str(job['status']))
            logging.info("Load took: " +str(job['output']['runtime']))
    elif job['status'] == 'running':
        if print_results == True:
            logging.info("Load result: " + str(job['status']))
            logging.info(str(job['progress']['complete'])+"/"+str(job['progress']['total'])+" task complete")
            logging.info("Status: "+str(job['progress']['message']))
    elif job['status'] == 'failed':
      failure_msg = retrieve_job_failure(uri, job['id'])
      logging.info("Job failed with error: "+ str(failure_msg['msg']))

def print_inputs(i):
    logging.info("Metadata URI: " + i['metadata_uri'])
    logging.info("database URI: " + i['database_uri'])
    logging.info("Ensembl release number: " + i['e_release'])
    logging.info("Release date: " + i['release_date'])
    logging.info("Is it the current release: " + i['current_release'])
    if 'eg_release' in i:
      logging.info("EG release number: " + i['eg_release'])
    logging.info("Email of submitter: " + i['email'])
    logging.info("Update_type: " + i['update_type'])
    logging.info("Comment: " + i['comment'])
    logging.info("Source: " + i['source'])

if __name__ == '__main__':
            
    parser = argparse.ArgumentParser(description='Metadata load via a REST service')

    parser.add_argument('-u', '--uri', help='Metadata database REST service URI', required=True)
    parser.add_argument('-a', '--action', help='Action to take', choices=['submit', 'retrieve', 'list', 'delete', 'email', 'kill_job'], required=True)
    parser.add_argument('-i', '--job_id', help='Metadata job identifier to retrieve')
    parser.add_argument('-v', '--verbose', help='Verbose output', action='store_true')
    parser.add_argument('-o', '--output_file', help='File to write output as JSON', type=argparse.FileType('w'))
    parser.add_argument('-f', '--input_file', help='File containing list of metadata and database URIs', type=argparse.FileType('r'))
    parser.add_argument('-m', '--metadata_uri', help='URI of metadata database')
    parser.add_argument('-d', '--database_uri', help='URI of database to load')
    parser.add_argument('-s', '--e_release', help='Ensembl release number')
    parser.add_argument('-r', '--release_date', help='Release date')
    parser.add_argument('-c', '--current_release', help='Is this the current release')
    parser.add_argument('-g', '--eg_release', help='EG release number')
    parser.add_argument('-e', '--email', help='Email where to send the report')
    parser.add_argument('-t', '--update_type', help='Update type, e.g: New assembly')
    parser.add_argument('-n', '--comment', help='Comment')
    parser.add_argument('-b', '--source', help='Source of the database, eg: Handover, Release load')



    args = parser.parse_args()
    
    if args.verbose == True:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s - %(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s - %(message)s')
    
    if args.uri.endswith('/') == False:
        args.uri = args.uri + '/'    
            
    if args.action == 'submit':

        if args.input_file == None:
            logging.info("Submitting " + args.database_uri + "->" + args.metadata_uri)
            id = submit_job(args.uri, args.metadata_uri, args.database_uri, args.e_release, args.eg_release, args.release_date, args.current_release, args.email, args.update_type, args.comment, args.source)
            logging.info('Job submitted with ID '+str(id))
        else:
            for line in args.input_file:
                uris = line.split()
                logging.info("Submitting " + uris[0] + "->" + uris[1])
                id = submit_job(args.uri, uris[0], uris[1], args.e_release, args.eg_release, args.release_date, args.current_release, args.email, args.update_type, args.comment, args.source)
                logging.info('Job submitted with ID '+str(id))
    
    elif args.action == 'retrieve':
    
        job = retrieve_job(args.uri, args.job_id, args.output_file)
        print_job(args.uri, job, print_results=True, print_input=True)
    
    elif args.action == 'list':
       
        jobs = list_jobs(args.uri, args.output_file)   
        for job in jobs:
            print_job(args.uri, job)
    
    elif args.action == 'delete':
        delete_job(args.uri, args.job_id)
        logging.info("Job " + str(args.job_id) + " was successfully deleted")

    elif args.action == 'email':
        results_email(args.uri, args.job_id, args.email)
        
