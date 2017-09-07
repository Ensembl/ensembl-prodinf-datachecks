#!/usr/bin/env python
from flask import Flask, request, jsonify
from flask_cors import CORS
from ensembl_prodinf.db_utils import list_databases
from ensembl_prodinf.server_utils import get_status
import json
import logging
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

app = Flask(__name__, instance_relative_config=True)
print app.config
app.config.from_object('db_config')
app.config.from_pyfile('db_config.py')

cors = CORS(app)

# use re to support different charsets
json_pattern = re.compile("application/json")

@app.route('/list_databases', methods=['GET'])
def list_databases_endpoint():
    try:
        db_uri = request.args.get('db_uri')
        query = request.args.get('query')
        return jsonify(list_databases(db_uri, query))
    except ValueError:
        return "Job "+str(job_id)+" not found", 404

@app.route('/status/<host>', methods=['GET'])
def get_status_endpoint(host):
    dir_name  = request.args.get('dir_name')
    if(dir_name == None):
        dir_name = '/instances'
    print dir_name
    print host
    return jsonify(get_status(host=host, dir_name=dir_name))

