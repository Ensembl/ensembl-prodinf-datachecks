#!/usr/bin/env python
from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine, text
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
def list_databases():
    try:
        db_uri = request.args.get('db_uri')
        query = request.args.get('query')
        logging.info("Looking up "+str(query)+" on "+str(db_uri))
        engine = create_engine(db_uri)
        s = text("select schema_name from information_schema.schemata where schema_name rlike :q")
        noms = []
        with engine.connect() as con:
            noms = [str(r[0]) for r in con.execute(s, {"q":query}).fetchall()]
        return jsonify(noms)
    except ValueError:
        return "Job "+str(job_id)+" not found", 404

