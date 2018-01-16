#!/usr/bin/env python
from flask import Flask, request, jsonify
from flask_cors import CORS
from ensembl_prodinf.db_utils import list_databases, get_database_sizes
from ensembl_prodinf.server_utils import get_status, get_load
from ensembl_prodinf import HiveInstance
from ensembl_prodinf.tasks import email_when_complete
from flasgger import Swagger
import logging
import re
import os
import signal
import time
import json
from macpath import dirname

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

app = Flask(__name__, instance_relative_config=True)
app.config['SWAGGER'] = {
    'title': 'Database copy REST endpoints',
    'uiversion': 2
}
app.config.from_object('db_config')
app.config.from_pyfile('db_config.py')
app.analysis = app.config["HIVE_ANALYSIS"]
print app.config
swagger = Swagger(app)

with open(app.config["SERVER_URIS_FILE"], 'r') as f:
    app.servers = json.loads(f.read())

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
    """
    Endpoint to retrieve a list of databases from a server given as URI
    This is using docstring for specifications
    ---
    tags:
      - list_databases
    parameters:
      - in : query
        name: db_uri
        type: string
        required: true
        default: mysql://user@server:port/
        description: MySQL server db_uri
      - in : query
        name: query
        type: string
        required: true
        default: homo_sapiens
        description: query use to find databases
    operationId: list_databases
    consumes:
      - application/json
    produces:
      - application/json
    security:
      list_databases_auth:
        - 'write:list_databases'
        - 'read:list_databases'
    schemes: ['http', 'https']
    deprecated: false
    externalDocs:
      description: Project repository
      url: http://github.com/rochacbruno/flasgger
    definitions:
      db_uri:
        type: db_uri
        properties:
          db_uri:
            type: string
            items:
              $ref: '#/definitions/db_uri'
      query:
        type: query
        properties:
          query:
            type: string
            items:
              $ref: '#/definitions/query'
      list_databases:
        type: object
        properties:
          list_databases:
            type: string
            items:
              $ref: '#/definitions/list_databases'
    responses:
      200:
        description: list_databases of a MySQL server
        schema:
          $ref: '#/definitions/list_databases'
        examples:
          ["homo_sapiens_cdna_91_38", "homo_sapiens_core_91_38","homo_sapiens_funcgen_91_38","homo_sapiens_otherfeatures_91_38","homo_sapiens_rnaseq_91_38","homo_sapiens_variation_91_38"]
    """
    try:
        db_uri = request.args.get('db_uri')
        query = request.args.get('query')
        logging.debug("Finding dbs matching " + query + " on " + db_uri)
        return jsonify(list_databases(db_uri, query))
    except Exception as e:
        return "Could not list databases: "+str(e), 500

@app.route('/database_sizes', methods=['GET'])
def database_sizes_endpoint():
    try:
        db_uri = request.args.get('db_uri')
        query = request.args.get('query')
        dir_name = request.args.get('dir_name')
        if(dir_name == None):
            dir_name = '/instances'
        logging.debug("Finding sizes of dbs matching " + str(query) + " on " + db_uri)
        return jsonify(get_database_sizes(db_uri, query, dir_name))
    except Exception as e:
        return "Could not list database sizes: "+str(e), 500

@app.route('/status/<host>', methods=['GET'])
def get_status_endpoint(host):
    """
    Endpoint to retrieve the status of a give MySQL host
    This is using docstring for specifications
    ---
    tags:
      - status
    parameters:
      - name: host
        in: path
        type: string
        required: true
        default: server_name
        description: MySQL server host name
    operationId: status
    consumes:
      - application/json
    produces:
      - application/json
    security:
      status_auth:
        - 'write:status'
        - 'read:status'
    schemes: ['http', 'https']
    deprecated: false
    externalDocs:
      description: Project repository
      url: http://github.com/rochacbruno/flasgger
    definitions:
      host:
        type: object
        properties:
          host:
            type: string
            items:
              $ref: '#/definitions/host'
      status:
        type: object
        properties:
          status:
            type: string
            items:
              $ref: '#/definitions/status'
    responses:
      200:
        description: Status of a MySQL server
        schema:
          $ref: '#/definitions/host'
        examples:
          dir: /instances 
          disk_available_g: 1504 
          disk_total_g: 6048 
          disk_used_g: 4258 
          disk_used_pct: 70.4 
          host: server_name 
          load_15m: 0.05 
          load_1m: 0.0 
          load_5m: 0.01 
          memory_available_m: 270 
          memory_total_m: 48394 
          memory_used_m: 23624 
          memory_used_pct: 48.8 
          n_cpus: 16
    """
    dir_name = request.args.get('dir_name')
    if(dir_name == None):
        dir_name = '/instances'
    logging.debug("Finding status of " + host + " (dir " + dir_name + ")")
    try:
        return jsonify(get_status(host=host, dir_name=dir_name))
    except Exception as e:
        return "Could not get status: "+str(e), 500

@app.route('/load/<host>', methods=['GET'])
def get_load_endpoint(host):
    """
    Endpoint to retrieve the load of a given MySQL server
    This is using docstring for specifications
    ---
    tags:
      - load
    parameters:
      - name: host
        in: path
        type: string
        required: true
        default: server_name
        description: MySQL server host name
    operationId: load
    consumes:
      - application/json
    produces:
      - application/json
    security:
      load_auth:
        - 'write:load'
        - 'read:load'
    schemes: ['http', 'https']
    deprecated: false
    externalDocs:
      description: Project repository
      url: http://github.com/rochacbruno/flasgger
    definitions:
      host:
        type: object
        properties:
          host:
            type: string
            items:
              $ref: '#/definitions/host'
      load:
        type: object
        properties:
          load:
            type: string
            items:
              $ref: '#/definitions/load'
    responses:
      200:
        description: Load of a MySQL server
        schema:
          $ref: '#/definitions/host'
        examples:
          load_15m: 0.05 
          load_1m: 0.05 
          load_5m: 0.03
    """
    logging.debug("Finding load of " + host)
    try:
        return jsonify(get_load(host=host))
    except Exception as e:
        return "Could not get status: "+str(e), 500


@app.route('/list_servers/<user>', methods=['GET'])
def list_servers_endpoint(user):
    """
    Endpoint to list the mysql servers accesible by a given user
    This is using docstring for specifications
    ---
    tags:
      - list_servers
    parameters:
      - name: user
        in: path
        type: string
        required: true
        default: ensro
        description: MySQL server user name
      - in: query
        name: query
        type: string
        required: true
        default: server_name
        description: MySQL server host name used to filter down the list
    operationId: list_servers
    consumes:
      - application/json
    produces:
      - application/json
    security:
      list_servers_auth:
        - 'write:list_servers'
        - 'read:list_servers'
    schemes: ['http', 'https']
    deprecated: false
    externalDocs:
      description: Project repository
      url: http://github.com/rochacbruno/flasgger
    definitions:
      user:
        type: object
        properties:
          user:
            type: string
            items:
              $ref: '#/definitions/user'
      query:
        type: object
        properties:
          query:
            type: string
            items:
              $ref: '#/definitions/query'
      list_servers:
        type: object
        properties:
          list_servers:
            type: string
            items:
              $ref: '#/definitions/list_servers'
    responses:
      200:
        description: list_servers of a MySQL server
        schema:
          $ref: '#/definitions/host'
        examples:
          ["mysql://user@server:port/"]
    """
    query = request.args.get('query')
    if query == None:
        return "Query not specified", 400
    if user in app.servers:
        logging.debug("Finding servers matching " + query + " for " + user)
        user_urls = app.servers[user] or []
        urls = filter(lambda x:query in x, user_urls)
        return jsonify(urls)
    else:
        return "User " + user + " not found", 404


@app.route('/submit', methods=['POST'])
def submit():
    """
    Endpoint to submit a database copy job
    This is using docstring for specifications
    ---
    tags:
      - submit
    parameters:
      - in: body
        name: body
        description: copy database job object
        requiered: false
        schema:
          $ref: '#/definitions/submit'
    operationId: submit
    consumes:
      - application/json
    produces:
      - application/json
    security:
      submit_auth:
        - 'write:submit'
        - 'read:submit'
    schemes: ['http', 'https']
    deprecated: false
    externalDocs:
      description: Project repository
      url: http://github.com/rochacbruno/flasgger
    definitions:
      submit:
        title: Database copy job
        description: A job to copy a database from a source MySQL server to a target MySQL server.
        type: object
        required: 
          -source_db_uri
          -target_db_uri
        properties:
          source_db_uri:
            type: string
            example: 'mysql://user@server:port/saccharomyces_cerevisiae_core_91_4'
          target_db_uri:
            type: string
            example: 'mysql://user:password@server:port/'
          only_tables:
            type: string
            example: 'undefined'
          skip_tables:
            type: string
            example: 'undefined'
          update:
            type: integer
            example: 0
          drop:
            type: integer
            example: 0
          email:
            type: string
            example: 'undefined'
    responses:
      200:
        description: submit of an healthcheck job
        schema:
          $ref: '#/definitions/submit'
        examples:
          {source_db_uri: "mysql://user@server:port/saccharomyces_cerevisiae_core_91_4", target_db_uri: "mysql://user:password@server:port/saccharomyces_cerevisiae_core_91_4", only_tables: undefined, skip_tables: undefined, update: undefined, drop: 1, email: undefined }
    """
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
    """
    Endpoint to retrieve a given job result using job_id
    This is using docstring for specifications
    ---
    tags:
      - results
    parameters:
      - name: job_id
        in: path
        type: integer
        required: true
        default: 1
        description: id of the job
    operationId: results
    consumes:
      - application/json
    produces:
      - application/json
    security:
      results_auth:
        - 'write:results'
        - 'read:results'
    schemes: ['http', 'https']
    deprecated: false
    externalDocs:
      description: Project repository
      url: http://github.com/rochacbruno/flasgger
    definitions:
      job_id:
        type: object
        properties:
          job_id:
            type: integer
            items:
              $ref: '#/definitions/job_id'
      result:
        type: object
        properties:
          result:
            type: string
            items:
              $ref: '#/definitions/result'
    responses:
      200:
        description: Result of an healthcheck job
        schema:
          $ref: '#/definitions/job_id'
        examples:
          id: 1 
          input: 
            drop: 1 
            source_db_uri: mysql://user@server:port/saccharomyces_cerevisiae_core_91_4 
            target_db_uri: mysql://user:password@server:port/saccharomyces_cerevisiae_core_91_4 
            timestamp: 1515494114.263158
          output: 
            runtime: 31 seconds 
            source_db_uri: mysql://user@server:port/saccharomyces_cerevisiae_core_91_4 
            target_db_uri: mysql://user:password@server:port/saccharomyces_cerevisiae_core_91_4
          status: complete
    """
    try:
        logging.info("Retrieving job with ID " + str(job_id))
        return jsonify(get_hive().get_result_for_job_id(job_id))
    except ValueError:
        return "Job " + str(job_id) + " not found", 404


@app.route('/failure/<int:job_id>', methods=['GET'])
def failure(job_id):
    """
    Endpoint to retrieve a given job failure using job_id
    This is using docstring for specifications
    ---
    tags:
      - failure
    parameters:
      - name: job_id
        in: path
        type: integer
        required: true
        default: 13
        description: id of the job
    operationId: failure
    consumes:
      - application/json
    produces:
      - application/json
    security:
      failure_auth:
        - 'write:failure'
        - 'read:failure'
    schemes: ['http', 'https']
    deprecated: false
    externalDocs:
      description: Project repository
      url: http://github.com/rochacbruno/flasgger
    definitions:
      job_id:
        type: object
        properties:
          job_id:
            type: integer
            items:
              $ref: '#/definitions/job_id'
      failure:
        type: object
        properties:
          failure:
            type: string
            items:
              $ref: '#/definitions/failure'
    responses:
      200:
        description: Retrieve failure of a given job using job_id
        schema:
          $ref: '#/definitions/job_id'
        examples:
          msg: 'Could not find myisamchk in PATH at /homes/ensdb-prod/ensembl-production/modules/Bio/EnsEMBL/Production/Pipeline/CopyDatabases/CopyDatabaseHive.pm line 80.'
    """
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
    """
    Endpoint to delete a given job result using job_id
    This is using docstring for specifications
    ---
    tags:
      - delete
    parameters:
      - name: job_id
        in: path
        type: integer
        required: true
        default: 1
        description: id of the job
    operationId: delete
    consumes:
      - application/json
    produces:
      - application/json
    security:
      delete_auth:
        - 'write:delete'
        - 'read:delete'
    schemes: ['http', 'https']
    deprecated: false
    externalDocs:
      description: Project repository
      url: http://github.com/rochacbruno/flasgger
    definitions:
      job_id:
        type: object
        properties:
          job_id:
            type: integer
            items:
              $ref: '#/definitions/job_id'
      id:
        type: integer
        properties:
          id:
            type: integer
            items:
              $ref: '#/definitions/id'
    responses:
      200:
        description: Job_id that has been deleted
        schema:
          $ref: '#/definitions/job_id'
        examples:
          id: 1
    """
    hive = get_hive()
    job = get_hive().get_job_by_id(job_id)
    if(job == None):
        return "Job " + str(job_id) + " not found", 404
    hive.delete_job(job)
    return jsonify({"id":job_id})


@app.route('/results_email/<int:job_id>', methods=['GET'])
def results_email(job_id):
    """
    Endpoint to display job result sent to email defined in input
    This is using docstring for specifications
    ---
    tags:
      - results_email
    parameters:
      - name: job_id
        in: path
        type: integer
        required: true
        default: 4
        description: id of the job
    operationId: results_email
    consumes:
      - application/json
    produces:
      - application/json
    security:
      results_email_auth:
        - 'write:results_email'
        - 'read:results_email'
    schemes: ['http', 'https']
    deprecated: false
    externalDocs:
      description: Project repository
      url: http://github.com/rochacbruno/flasgger
    definitions:
      job_id:
        type: object
        properties:
          job_id:
            type: integer
            items:
              $ref: '#/definitions/job_id'
      results_email:
        type: string
        properties:
          results_email:
            type: string
            items:
              $ref: '#/definitions/results_email'
    responses:
      200:
        description: result in email friendly format that was sent to email defined in input
        schema:
          $ref: '#/definitions/job_id'
        examples:
          body: 'Copy from mysql://user@server:port/saccharomyces_cerevisiae_core_91_4 to mysql://user:password@server:port/saccharomyces_cerevisiae_core_91_4 is successful Copy took 31 seconds' 
          id: 1
          input: 
            drop: 1 
            source_db_uri: mysql://user@server:port/saccharomyces_cerevisiae_core_91_4 
            target_db_uri: mysql://user:password@server:port/saccharomyces_cerevisiae_core_91_4 
            timestamp: 1515494114.263158
          output: null 
          status: complete 
          subject: 'Copy database from mysql://user@server:port/saccharomyces_cerevisiae_core_91_4 to mysql://user:password@server:port/saccharomyces_cerevisiae_core_91_4 successful'
    """
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
    """
    Endpoint to retrieve all the jobs results from the database
    This is using docstring for specifications
    ---
    tags:
      - jobs
    operationId: jobs
    consumes:
      - application/json
    produces:
      - application/json
    security:
      jobs_auth:
        - 'write:jobs'
        - 'read:jobs'
    schemes: ['http', 'https']
    deprecated: false
    externalDocs:
      description: Project repository
      url: http://github.com/rochacbruno/flasgger
    responses:
      200:
        description: Retrieve all the jobs results from the database
        schema:
          $ref: '#/definitions/job_id'
        examples:
          id: 1 
          input: 
            drop: 1 
            source_db_uri: mysql://user@server:port/saccharomyces_cerevisiae_core_91_4 
            target_db_uri: mysql://user:password@server:port/saccharomyces_cerevisiae_core_91_4 
            timestamp: 1515494114.263158  
          output: 
            runtime: 31 seconds 
            source_db_uri: mysql://user@server:port/saccharomyces_cerevisiae_core_91_4 
            target_db_uri: mysql://user:password@server:port/saccharomyces_cerevisiae_core_91_4     
          status: complete
          id: 2 
          input: 
            drop: 1 
            email: john.doe@ebi.ac.uk 
            source_db_uri: mysql://user@server:port/saccharomyces_cerevisiae_core_91_4 
            target_db_uri: mysql://user:password@server:port/saccharomyces_cerevisiae_core_91_4 
            timestamp: 1515494178.544427  
          output: 
            runtime: 31 seconds 
            source_db_uri: mysql://user@server:port/saccharomyces_cerevisiae_core_91_4 
            target_db_uri: mysql://user:password@server:port/saccharomyces_cerevisiae_core_91_4  
          status: complete
          id: 3 
          input: 
            drop: 1 
            email: john.doe@ebi.ac.uk 
            source_db_uri: mysql://user@server:port/saccharomyces_cerevisiae_core_91_4 
            target_db_uri: mysql://user:password@server:port/saccharomyces_cerevisiae_core_91_4 
            timestamp: 1515602446.492586  
          progress: 
            complete: 0 
            total: 1
          status: failed
    """
    logging.info("Retrieving jobs")
    return jsonify(get_hive().get_all_results(app.analysis))

if __name__ == "__main__":
    app.run(debug=True)