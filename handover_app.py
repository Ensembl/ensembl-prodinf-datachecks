#!/usr/bin/env python
from flask import Flask, request, jsonify
from flask_cors import CORS
from flasgger import Swagger
import logging
import re

from ensembl_prodinf.handover_tasks import handover_database

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

app = Flask(__name__, instance_relative_config=True)
app.config.from_object('handover_config')
app.config.from_pyfile('handover_config.py')
swagger = Swagger(app)
cors = CORS(app)

# use re to support different charsets
json_pattern = re.compile("application/json")

@app.route('/', methods=['GET'])
def info():
    app.config['SWAGGER']= {'title': 'Handover REST endpoints','uiversion': 2}
    return jsonify(app.config['SWAGGER'])

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({"status":"ok"})

@app.route('/submit', methods=['POST'])
def handover():
    """
    Endpoint to submit an handover job
    This is using docstring for specifications
    ---
    tags:
      - submit
    parameters:
      - in: body
        name: body
        description: healthcheck object
        required: false
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
        title: handover job
        description: A job to handover a database, the database will be healthchecked, copied and added to metadata database
        type: object
        required: 
          -src_uri
          -contact
          -type
          -comment
        properties:
          src_uri:
            type: string
            example: 'mysql://user@server:port/saccharomyces_cerevisiae_core_91_4'
          type:
            type: string
            example: 'other'
          comment:
            type: string
            example: 'handover new Panda OF'
          contact:
            type: string
            example: 'joe.blogg@ebi.ac.uk'
    responses:
      200:
        description: submit of an healthcheck job
        schema:
          $ref: '#/definitions/submit'
        examples:
          {src_uri: "mysql://user@server:port/saccharomyces_cerevisiae_core_91_4", contact: "joe.blogg@ebi.ac.uk", type: "other", comment: "handover new Panda OF"}
    """
    if json_pattern.match(request.headers['Content-Type']):

        logging.debug("Submitting handover request " + str(request.json))
        spec = request.json

        if 'src_uri' not in spec or 'contact' not in spec or 'type' not in spec or 'comment' not in spec:
            return "Handover specification incomplete - please specify src_uri, contact, type and comment", 415

        ticket = handover_database(spec)
        logging.info(ticket)
        return jsonify(ticket);
    
    else:
        return "Could not handle input of type " + request.headers['Content-Type'], 415

