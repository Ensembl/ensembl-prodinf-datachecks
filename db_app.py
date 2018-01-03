#!/usr/bin/env python
from flask import Flask, request, jsonify
from flask_cors import CORS
from ensembl_prodinf.db_utils import list_databases
from ensembl_prodinf.server_utils import get_status, get_load, get_database_sizes
from ensembl_prodinf import HiveInstance
from ensembl_prodinf.tasks import email_when_complete
import logging
import re
import os
import signal
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

app = Flask(__name__, instance_relative_config=True)
print app.config
app.config.from_object('db_config')
app.config.from_pyfile('db_config.py')
app.analysis = app.config["HIVE_ANALYSIS"]

hive = None


def get_hive():
    global hive
    if hive == None:
        hive = HiveInstance(app.config["HIVE_URI"])
    return hive


def is_running(pid):
    try:
        os.kill(pid, 0)
    except OSError as err:
        return False
    return True


cors = CORS(app)

# use re to support different charsets
json_pattern = re.compile("application/json")


@app.route('/list_databases', methods=['GET'])
def list_databases_endpoint():
    try:
        db_uri = request.args.get('db_uri')
        query = request.args.get('query')
        logging.debug("Finding dbs matching " + query + " on " + db_uri)
        return jsonify(list_databases(db_uri, query))
    except ValueError:
        return "Could not list databases", 500

@app.route('/databases/sizes', methods=['GET'])
def databases_sizes_endpoint(host, port):
    try:
        dir_name = request.args.get('dir_name')
        if(dir_name == None):
            dir_name = '/instances/' + str(port)
        logging.debug("Finding database sizes for "+host+":"+port)
        return jsonify(get_database_sizes(host,dir_name))
    except ValueError:
        return "Could not list database sizes", 500


@app.route('/status/<host>', methods=['GET'])
def get_status_endpoint(host):
    dir_name = request.args.get('dir_name')
    if(dir_name == None):
        dir_name = '/instances'
    logging.debug("Finding status of " + host + " (dir " + dir_name + ")")
    return jsonify(get_status(host=host, dir_name=dir_name))


@app.route('/load/<host>', methods=['GET'])
def get_load_endpoint(host):
    logging.debug("Finding load of " + host)
    return jsonify(get_load(host=host))


@app.route('/list_servers/<user>', methods=['GET'])
def list_servers_endpoint(user):
    query = request.args.get('query')
    servers = app.config["SERVER_URIS"]
    if user in servers:
        logging.debug("Finding servers matching " + query + " for " + user)
        user_urls = servers[user] or []
        urls = filter(lambda x:query in x, user_urls)
        return jsonify(urls)
    else:
        return "User " + user + " not found", 404


@app.route('/submit', methods=['POST'])
def submit():
    if json_pattern.match(request.headers['Content-Type']):
        logging.debug("Submitting Database copy " + str(request.json))
        job = get_hive().create_job(app.analysis, request.json)
        results = {"job_id":job.job_id};
        email = request.json.get('email')
        if email != None and email != '':
            logging.debug("Submitting email request for  " + email)
            email_results = email_when_complete.delay(request.url_root + "results_email/" + str(job.job_id), email)
            results['email_task'] = email_results.id
        return jsonify(results);
    else:
        return "Could not handle input of type " + request.headers['Content-Type'], 415


@app.route('/results/<int:job_id>', methods=['GET'])
def results(job_id):
    try:
        logging.info("Retrieving job with ID " + str(job_id))
        return jsonify(get_hive().get_result_for_job_id(job_id))
    except ValueError:
        return "Job " + str(job_id) + " not found", 404


@app.route('/failure/<int:job_id>', methods=['GET'])
def failure(job_id):
    try:
        logging.info("Retrieving failure for job with ID " + str(job_id))
        failure = get_hive().get_job_failure_msg_by_id(job_id)
        return jsonify({"msg":failure.msg})
    except ValueError:
        return "Job " + str(job_id) + " not found", 404


@app.route('/kill_job/<int:job_id>', methods=['GET'])
def kill_job(job_id):
    hive = get_hive()
    job = get_hive().get_job_by_id(job_id)
    if(job == None):
        return "Job " + str(job_id) + " not found", 404
    logging.debug("Getting worker_id for job_id " + str(job_id))
    worker = get_hive().get_worker_id(job.role_id)
    logging.debug("Getting process_id for worker_id " + str(worker.worker_id))
    process_id = get_hive().get_worker_process_id(worker.worker_id)
    logging.debug("Process_id is " + str(process_id.process_id))
    os.kill(int(process_id.process_id), signal.SIGTERM)
    time.sleep(5)
    # Check if the process that we killed is alive.
    if (is_running(int(process_id.process_id))):
        return "Wasn't able to kill the process: " + str(process_id.process_id), 404
    else:
        return jsonify({"process_id":process_id.process_id})


@app.route('/delete/<int:job_id>', methods=['GET'])
def delete(job_id):
    hive = get_hive()
    job = get_hive().get_job_by_id(job_id)
    if(job == None):
        return "Job " + str(job_id) + " not found", 404
    hive.delete_job(job)
    return jsonify({"id":job_id})


@app.route('/results_email/<int:job_id>', methods=['GET'])
def results_email(job_id):
    email = request.args.get('email')
    logging.info("Retrieving job with ID " + str(job_id) + " for " + str(email))
    job = get_hive().get_job_by_id(job_id)
    if(job == None):
        return "Job " + str(job_id) + " not found", 404
    results = get_hive().get_result_for_job_id(job_id)
    if results['status'] == 'complete':
        results['subject'] = 'Copy database from %s to %s successful' % (results['output']['source_db_uri'], results['output']['target_db_uri'])
        results['body'] = "Copy from %s to %s is successful\n" % (results['output']['source_db_uri'], results['output']['target_db_uri'])
        results['body'] += "Copy took %s" % (results['output']['runtime'])
    elif results['status'] == 'failed':
        failure = get_hive().get_job_failure_msg_by_id(job_id)
        results['subject'] = 'Copy database from %s to %s failed' % (results['input']['source_db_uri'], results['input']['target_db_uri'])
        results['body'] = 'Copy failed with following message:\n'
        results['body'] += '%s' % (failure.msg)
    results['output'] = None
    return jsonify(results)


@app.route('/jobs', methods=['GET'])
def jobs():
    logging.info("Retrieving jobs")
    return jsonify(get_hive().get_all_results(app.analysis))

