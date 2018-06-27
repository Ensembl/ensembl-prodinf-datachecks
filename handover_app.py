#!/usr/bin/env python
from flask import Flask, request, jsonify
from flask_cors import CORS
from flasgger import Swagger
import logging
import re
import requests
import json
from ensembl_prodinf.handover_tasks import handover_database
from elasticsearch import Elasticsearch



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

@app.route('/handovers', methods=['POST'])
def handovers():
    """
    Endpoint to submit an handover job
    This is using docstring for specifications
    ---
    tags:
      - handovers
    parameters:
      - in: body
        name: body
        description: healthcheck object
        required: false
        schema:
          $ref: '#/definitions/handovers'
    operationId: handovers
    consumes:
      - application/json
    produces:
      - application/json
    security:
      handovers_auth:
        - 'write:handovers'
        - 'read:handovers'
    schemes: ['http', 'https']
    deprecated: false
    externalDocs:
      description: Project repository
      url: http://github.com/rochacbruno/flasgger
    definitions:
      handovers:
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
        description: submit of an handover job
        schema:
          $ref: '#/definitions/handovers'
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

@app.route('/handovers/<string:handover_token>', methods=['GET'])
def handover_result(handover_token):
    """
    Endpoint to get an handover job detail
    This is using docstring for specifications
    ---
    tags:
      - handovers
    parameters:
      - name: handover_token
        in: path
        type: string
        required: true
        default: 15ce20fd-68cd-11e8-8117-005056ab00f0
        description: handover token for the database handed over
    operationId: handovers
    consumes:
      - application/json
    produces:
      - application/json
    security:
      handovers_auth:
        - 'write:handovers'
        - 'read:handovers'
    schemes: ['http', 'https']
    deprecated: false
    externalDocs:
      description: Project repository
      url: http://github.com/rochacbruno/flasgger
    definitions:
      handovers:
        title: Get a handover job details
        description: This will retrieve a handover job details
        type: object
        required: 
          -handover_token
        properties:
          handover_token:
            type: string
            example: '15ce20fd-68cd-11e8-8117-005056ab00f0'
    responses:
      200:
        description: Retrieve an handover job ticket
        schema:
          $ref: '#/definitions/handovers'
        examples:
          [{"comment": "handover new Tiger database", "contact": "maurel@ebi.ac.uk", "handover_token": "605f1191-7a13-11e8-aa7e-005056ab00f0", "id": "X1qcQWQBiZ0vMed2vaAt", "message": "Metadata load complete, Handover successful", "progress_total": 3, "report_time": "2018-06-27T15:19:08.459", "src_uri": "mysql://ensadmin:ensembl@mysql-ens-general-prod-1:4525/panthera_tigris_altaica_core_93_1", "tgt_uri": "mysql://ensadmin:ensembl@mysql-ens-general-dev-1:4484/panthera_tigris_altaica_core_93_1", "type": "new_assembly"} ]
    """
    try:
        res = requests.get('http://localhost:9200')
    except ValueError:
      return "Can't connect to Elasticsearch"
    try:    
        logging.info("Retrieving handover data with token " + str(handover_token))
        es = Elasticsearch([{'host': 'localhost', 'port': 9200}])
        res=es.search(index="reports",body={"query":{"bool":{"must":[{"term":{"params.handover_token.keyword":str(handover_token)}},{"term":{"report_type.keyword":"INFO"}}],"must_not":[],"should":[]}},"from":0,"size":1,"sort":[{"report_time":{"order": "desc"}}],"aggs":{}})
        handover_detail=make_list_results(res)
        return jsonify(handover_detail)
    except ValueError:
        return "Handover token " + str(handover_token) + " not found", 404

@app.route('/handovers/', methods=['GET'])
def handover_results():
    """
    Endpoint to get an handover job detail
    This is using docstring for specifications
    ---
    tags:
      - handovers
    operationId: handovers
    consumes:
      - application/json
    produces:
      - application/json
    security:
      handovers_auth:
        - 'write:handovers'
        - 'read:handovers'
    schemes: ['http', 'https']
    deprecated: false
    externalDocs:
      description: Project repository
      url: http://github.com/rochacbruno/flasgger
    definitions:
      handovers:
        title: Retrieve a list of handover databases
        description: This will retrieve all the handover job details
        type: object
    responses:
      200:
        description: Retrieve all the handover job details
        schema:
          $ref: '#/definitions/handovers'
        examples:
          [{"comment": "handover new Tiger database", "contact": "maurel@ebi.ac.uk", "handover_token": "605f1191-7a13-11e8-aa7e-005056ab00f0", "id": "QFqRQWQBiZ0vMed2vKDI", "message": "Handling {u'comment': u'handover new Tiger database', 'handover_token': '605f1191-7a13-11e8-aa7e-005056ab00f0', u'contact': u'maurel@ebi.ac.uk', u'src_uri': u'mysql://ensadmin:ensembl@mysql-ens-general-prod-1:4525/panthera_tigris_altaica_core_93_1', 'tgt_uri': 'mysql://ensadmin:ensembl@mysql-ens-general-dev-1:4484/panthera_tigris_altaica_core_93_1', u'type': u'new_assembly'}", "report_time": "2018-06-27T15:07:07.462", "src_uri": "mysql://ensadmin:ensembl@mysql-ens-general-prod-1:4525/panthera_tigris_altaica_core_93_1", "tgt_uri": "mysql://ensadmin:ensembl@mysql-ens-general-dev-1:4484/panthera_tigris_altaica_core_93_1", "type": "new_assembly"}, {"comment": "handover new Leopard database", "contact": "maurel@ebi.ac.uk", "handover_token": "5dcb1aca-7a13-11e8-b24e-005056ab00f0", "id": "P1qRQWQBiZ0vMed2rqBh", "message": "Handling {u'comment': u'handover new Leopard database', 'handover_token': '5dcb1aca-7a13-11e8-b24e-005056ab00f0', u'contact': u'maurel@ebi.ac.uk', u'src_uri': u'mysql://ensadmin:ensembl@mysql-ens-general-prod-1:4525/panthera_pardus_core_93_1', 'tgt_uri': 'mysql://ensadmin:ensembl@mysql-ens-general-dev-1:4484/panthera_pardus_core_93_1', u'type': u'new_assembly'}", "report_time": "2018-06-27T15:07:03.145", "src_uri": "mysql://ensadmin:ensembl@mysql-ens-general-prod-1:4525/panthera_pardus_core_93_1", "tgt_uri": "mysql://ensadmin:ensembl@mysql-ens-general-dev-1:4484/panthera_pardus_core_93_1", "type": "new_assembly"} ]
    """
    try:
        res = requests.get('http://localhost:9200')
    except ValueError:
      return "Can't connect to Elasticsearch"
    try:    
        logging.info("Retrieving all handover report")
        es = Elasticsearch([{'host': 'localhost', 'port': 9200}])
        res = es.search(index="reports",body={"query": {"bool": {"must": [{"query_string" : {"fields": ["message"],"query" : "Handling*","analyze_wildcard": "true"}}]}},"size":1000,"sort":[{"report_time":{"order": "desc"}}]})
        list_handovers=make_list_results(res)
        return jsonify(list_handovers)
    except ValueError:
        return "Handover token data not found", 404

@app.route('/handovers/<string:handover_token>', methods=['DELETE'])
def delete_handover(handover_token):
    """
    Endpoint to delete all the reports linked to a handover_token
    This is using docstring for specifications
    ---
    tags:
      - handovers
    parameters:
      - name: handover_token
        in: path
        type: string
        required: true
        default: 15ce20fd-68cd-11e8-8117-005056ab00f0
        description: handover token for the database handed over
    operationId: handovers
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
      handover_token:
        type: object
        properties:
          handover_token:
            type: integer
            items:
              $ref: '#/definitions/handover_token'
      id:
        type: integer
        properties:
          id:
            type: integer
            items:
              $ref: '#/definitions/id'
    responses:
      200:
        description: handover_token of the reports that need deleting
        schema:
          $ref: '#/definitions/handover_token'
        examples:
          id: 15ce20fd-68cd-11e8-8117-005056ab00f0
    """
    try:
        res = requests.get('http://localhost:9200')
    except ValueError:
      return "Can't connect to Elasticsearch"
    try:
        logging.info("Retrieving handover data with token " + str(handover_token))
        es = Elasticsearch([{'host': 'localhost', 'port': 9200}])
        es.delete_by_query(index='reports', doc_type='report', body={"query":{"bool":{"must":[{"term":{"params.handover_token.keyword":str(handover_token)}}]}}})
        return jsonify(str(handover_token))
    except ValueError:
        return "Handover token " + str(handover_token) + " not found", 404

def make_list_results(res):
    list_results=[]
    for doc in res['hits']['hits']:
        result={"id":doc['_id']}
        result['message']=doc['_source']['message']
        result['comment']=doc['_source']['params']['comment']
        result['handover_token']=doc['_source']['params']['handover_token']
        result['contact']=doc['_source']['params']['contact']
        result['src_uri']=doc['_source']['params']['src_uri']
        result['tgt_uri']=doc['_source']['params']['tgt_uri']
        try:
            result['progress_complete']=doc['_source']['params']['progress_complete']
        except:
            pass
        try:
            result['progress_total']=doc['_source']['params']['progress_total']
        except:
            pass
        result['report_time']=doc['_source']['report_time']
        result['type']=doc['_source']['params']['type']
        list_results.append(result)
    return list_results