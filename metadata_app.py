#!/usr/bin/env python
from flask import Flask, request, jsonify
from flask_cors import CORS
from ensembl_prodinf import HiveInstance
from ensembl_prodinf.email_tasks import email_when_complete
from flasgger import Swagger
import logging
import re
import os
import signal
import time
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

app = Flask(__name__, instance_relative_config=True)
app.config.from_object('metadata_config')
app.config.from_pyfile('metadata_config.py', silent=True)
app.analysis = app.config["HIVE_ANALYSIS"]
app.config['SWAGGER'] = {
    'title': 'Metadata updater REST endpoints',
    'uiversion': 2
}
print app.config
swagger = Swagger(app)

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

@app.route('/submit', methods=['POST'])
def submit():
    """
    Endpoint to submit a database to be processed and added to the metadata database
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
        description: A job to process a database and add it to the metadata database from a source MySQL server to a target MySQL server.
        type: object
        required: 
          -metadata_uri
          -database_uri
          -e_release
          -release_date
          -current_release
        properties:
          metadata_uri:
            type: string
            example: 'mysql://user:password@server:port/metadata_db'
          database_uri:
            type: string
            example: 'mysql://user:password@server:port/db'
          e_release:
            type: integer
            example: 91
          eg_release:
            type: integer
            example: 38
          release_date:
            type: string
            example: '2017-12-06'
          current_release:
            type: integer
            example: 1
          email:
            type: string
            example: 'undefined'
    responses:
      200:
        description: submit of a metadata job
        schema:
          $ref: '#/definitions/submit'
        examples:
          {metadata_uri : "mysql://user:pass@mysql-ens-general-dev-1:4484/ensembl_metadata_new_test", database_uri : "mysql://ensro@mysql-ensembl-mirror:4240/octodon_degus_otherfeatures_91_1", e_release : 91, release_date : "2017-12-06", current_release : 1, email : "undefined"}
    """
    if json_pattern.match(request.headers['Content-Type']):
        logging.debug("Submitting metadata job " + str(request.json))
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
        description: Result of a metadata job
        schema:
          $ref: '#/definitions/job_id'
        examples:
          id: 1 
          input: 
            metadata_uri: mysql://user:password@server:port/ensembl_metadata 
            database_uri: mysql://user:password@server:port/saccharomyces_cerevisiae_core_91_4 
            timestamp: 1515494114.263158
          output: 
            runtime: 31 seconds 
            metadata_uri: mysql://user:password@server:port/ensembl_metadata 
            database_uri: mysql://user:password@server:port/saccharomyces_cerevisiae_core_91_4
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
          msg: 'Missing table meta in database'
    """
    try:
        logging.info("Retrieving failure for job with ID " + str(job_id))
        failure = get_hive().get_job_failure_msg_by_id(job_id)
        return jsonify({"msg":failure.msg})
    except ValueError:
        return "Job " + str(job_id) + " not found", 404

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
          body: 'Metadata load of mysql://user@server:port/saccharomyces_cerevisiae_core_91_4 in mysql://user:password@server:port/ensembl_metadata is successful. Load took 31 seconds' 
          id: 1
          input: 
            metadata_uri: mysql://user:password@server:port/ensembl_metadata
            database_uri: mysql://user:password@server:port/saccharomyces_cerevisiae_core_91_4 
            timestamp: 1515494114.263158
          output: null 
          status: complete 
          subject: 'Load of mysql://user@server:port/saccharomyces_cerevisiae_core_91_4 to mysql://user:password@server:port/saccharomyces_cerevisiae_core_91_4 successful'
    """
    email = request.args.get('email')
    logging.info("Retrieving job with ID " + str(job_id) + " for " + str(email))
    job = get_hive().get_job_by_id(job_id)
    if(job == None):
        return "Job " + str(job_id) + " not found", 404
    results = get_hive().get_result_for_job_id(job_id)
    if results['status'] == 'complete':
        results['subject'] = 'Metadata load of database %s to %s successful' % (results['output']['database_uri'], results['output']['metadata_uri'])
        results['body'] = "Meatadata load of database %s to %s is successful\n" % (results['output']['database_uri'], results['output']['metadata_uri'])
        results['body'] += "Load took %s" % (results['output']['runtime'])
    elif results['status'] == 'failed':
        failure = get_hive().get_job_failure_msg_by_id(job_id)
        results['subject'] = 'Metadata load of database %s to %s failed' % (results['input']['database_uri'], results['input']['metadata_uri'])
        results['body'] = 'Metadata load failed with:\n'
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
            metadata_uri: mysql://user@server:port/ensembl_metadata 
            database_uri: mysql://user:password@server:port/saccharomyces_cerevisiae_core_91_4 
            timestamp: 1515494114.263158  
          output: 
            runtime: 31 seconds 
            metadata_uri: mysql://user@server:port/ensembl_metadata
            database_uri: mysql://user:password@server:port/saccharomyces_cerevisiae_core_91_4     
          status: complete
          id: 2 
          input: 
            email: john.doe@ebi.ac.uk 
            metadata_uri: mysql://user@server:port/ensembl_metadata 
            database_uri: mysql://user:password@server:port/saccharomyces_cerevisiae_core_91_4 
            timestamp: 1515494178.544427  
          output: 
            runtime: 31 seconds 
            metadata_uri: mysql://user@server:port/ensembl_metadata  
            database_uri: mysql://user:password@server:port/saccharomyces_cerevisiae_core_91_4  
          status: complete
          id: 3 
          input: 
            email: john.doe@ebi.ac.uk 
            metadata_uri: mysql://user@server:port/ensembl_metadata
            database_uri: mysql://user:password@server:port/saccharomyces_cerevisiae_core_91_4 
            timestamp: 1515602446.492586  
          progress: 
            complete: 0 
            total: 1
          status: failed
    """
    logging.info("Retrieving jobs")
    return jsonify(get_hive().get_all_results_children(app.analysis))

if __name__ == "__main__":
    app.run(debug=True)
