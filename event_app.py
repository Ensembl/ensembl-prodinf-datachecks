#!/usr/bin/env python
from flask import Flask, request, jsonify
from flask_cors import CORS
from ensembl_prodinf import reporting
import re
import json

from ensembl_prodinf import HiveInstance
import event_config

pool = reporting.get_pool(event_config.report_server)
     
def get_logger():    
    return reporting.get_logger(pool, event_config.report_exchange, 'event_handler', None, {})

app = Flask(__name__, instance_relative_config=True)
print app.config
app.config.from_object('event_config')
app.config.from_pyfile('event_config.py')


class EventNotFoundError(Exception):
    """Exception showing event not found"""        

print event_config.event_lookup
event_lookup = json.loads(open(event_config.event_lookup).read())


def get_processes_for_event(event):
    event_type = event['type']
    if event_type not in event_lookup.keys():
        raise EventNotFoundError("Event type " + str(event_type) + " not known")
    return event_lookup[event_type]    


class ProcessNotFoundError(Exception):
    """Exception showing process not found"""


process_lookup = json.loads(open(event_config.process_lookup).read())


def get_analysis(process):
    if process not in process_lookup.keys():
        raise ProcessNotFoundError("Process " + str(process) + " not known")
    return process_lookup[process]['analysis']

hives = {}


def get_hive(process):    
    if process not in hives.keys():
        if process not in process_lookup.keys():
            raise ProcessNotFoundError("Process " + str(process) + " not known")
        hives[process] = HiveInstance(process_lookup[process]['hive_uri'])
    return hives[process]


cors = CORS(app)

# use re to support different charsets
json_pattern = re.compile("application/json")

@app.route('/jobs', methods=['POST'])
def submit_job():
    if json_pattern.match(request.headers['Content-Type']):
        event = request.json['event']
        results = {"processes":[], "event":event}
        # convert event to processes
        processes = get_processes_for_event(event)
        for process in processes:
            get_logger().debug("Submitting process " + str(process))
            try:
                hive = get_hive(process)
                analysis = get_analysis(process)
                job = hive.create_job(analysis, {'event':event})
                results['processes'].append({
                    "process":process,
                    "job":job.job_id
                })
            except ProcessNotFoundError:
                return "Process " + str(process) + " not found", 404
        return jsonify(results);
    else:
        return "Could not handle input of type " + request.headers['Content-Type'], 415


@app.route('/jobs/<string:process>/<int:job_id>', methods=['GET'])
def job(process, job_id):
    output_format = request.args.get('format')
    if output_format == 'email':
        email = request.args.get('email')
        if email == None:
            return "Email not specified", 400
        return results_email(request.args.get('email'), process, job_id)
    elif output_format == None:
        return results(process, job_id)
    else:
        return "Format "+output_format+" not known", 400
        
def results(process, job_id):    
    try:
        get_logger().info("Retrieving job from " + process + " with ID " + str(job_id))
        return jsonify(get_hive(process).get_result_for_job_id(job_id))
    except ValueError:
        return "Job " + str(job_id) + " not found for process " + process, 404


@app.route('/jobs/<string:process>/<int:job_id>', methods=['DELETE'])
def delete_job(process, job_id):
    hive = get_hive(process)
    job = hive.get_job_by_id(job_id)
    if(job == None):
        return "Job " + str(job_id) + " not found for process " + process, 404
    hive.delete_job(job)
    return jsonify({"id":job_id, "process": process})

def results_email(email, process, job_id):
    get_logger().info("Retrieving job with ID " + str(job_id) + " for " + str(email))
    hive = get_hive(process)
    job = hive.get_job_by_id(job_id)
    if(job == None):
        return "Job " + str(job_id) + " not found", 404
    results = hive.get_result_for_job_id(job_id)
    # TODO
    results['email'] = email
    return jsonify(results)

@app.route('/jobs/<string:process>', methods=['GET'])
def jobs(process):
    get_logger().info("Retrieving jobs")
    return jsonify(get_hive(process).get_all_results(get_analysis(process)))


@app.route('/events')
def events():
    return jsonify(event_lookup.keys()) 

@app.route('/processes')
def processes():
    return jsonify(process_lookup.keys()) 