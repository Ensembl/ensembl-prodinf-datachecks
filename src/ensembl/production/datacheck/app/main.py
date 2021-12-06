# See the NOTICE file distributed with this work for additional information
#    regarding copyright ownership.
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#        http://www.apache.org/licenses/LICENSE-2.0
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
import os
import re
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import requests
from ensembl.production.core.db_utils import get_databases_list, get_db_type
from ensembl.production.core.exceptions import HTTPRequestError
from ensembl.production.core.models.hive import HiveInstance
from ensembl.production.core.server_utils import assert_mysql_uri, assert_mysql_db_uri
from flasgger import Swagger
from flask import Flask, json, jsonify, render_template, request, send_file, redirect, flash, abort
from flask_bootstrap import Bootstrap
from flask_cors import CORS
from requests.exceptions import HTTPError
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.wrappers import Response

import ensembl.production.datacheck.exceptions
from ensembl.production.datacheck.config import DatacheckConfig
from ensembl.production.datacheck.forms import DatacheckSubmissionForm
from ensembl.production.datacheck.exceptions import MissingIndexException

# Go up two levels to get to root, where we will find the static and template files
app_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
static_path = os.path.join(app_path, 'static')
template_path = os.path.join(app_path, 'templates')

app = Flask(__name__,
            static_url_path='/static/datachecks/',
            static_folder=static_path,
            template_folder=template_path)

app.config.from_object(DatacheckConfig)

Bootstrap(app)
CORS(app)
Swagger(app, template_file=app.config['SWAGGER_FILE'])

app.analysis = app.config['HIVE_ANALYSIS']
app.index = app.config['DATACHECK_INDEX']
app.server_names = json.load(open(os.path.join(app_path, app.config['SERVER_NAMES_FILE'])))

app.names_list = []
app.groups_list = []
app.servers_list = []
app.servers_dict = {}

if app.env == 'development':
    # ENV dev (assumed run from builtin server, so update script_name at wsgi level)
    app.wsgi_app = DispatcherMiddleware(
        Response('Not Found', status=404),
        {app.config['SCRIPT_NAME']: app.wsgi_app}
    )


@app.context_processor
def inject_configs():
    return dict(script_name=app.config['SCRIPT_NAME'])


def get_names_list():
    if not app.index:
        # Empty list of compara
        raise MissingIndexException

    if not app.names_list:
        for name, params in app.index.items():
            app.names_list.append(name)
        app.names_list.sort()
    return app.names_list


def get_groups_list():
    if not app.index:
        # Empty list of compara
        raise MissingIndexException

    if not app.groups_list:
        groups_set = []
        for name, params in app.index.items():
            for group in params['groups']:
                groups_set.append(group)
        app.groups_list = sorted(set(groups_set))
    return app.groups_list


def get_servers_list():
    if not app.servers_list:
        app.servers_list = sorted(set(app.server_names))
    return app.servers_list


def get_servers_dict():
    if not app.servers_dict:
        app.servers_dict = app.server_names
    return app.servers_dict


hive = None


def get_hive():
    global hive
    if hive is None:
        hive = HiveInstance(app.config['HIVE_URI'])
    return hive


@app.route('/', methods=['GET'])
def index():
    return jsonify({'title': 'Datacheck REST endpoints', 'uiversion': 2})


@app.route('/servers/list', methods=['GET'])
def servers_list():
    return jsonify(get_servers_list())


@app.route('/servers/dict', methods=['GET'])
def servers_dict():
    return jsonify(get_servers_dict())


@app.route('/databases/list', methods=['GET'])
def databases_list():
    db_uri = request.args.get('db_uri')
    query = request.args.get('query')
    return jsonify(get_databases_list(db_uri, query))


@app.route('/names/', methods=['GET'])
@app.route('/names/<string:name_param>', methods=['GET'])
def names(name_param=None):
    if not app.index:
        # Empty list of compara
        raise MissingIndexException

    if name_param is None:
        index_names = app.index
    else:
        index_names = {}
        for name, params in app.index.items():
            if name == name_param:
                index_names.setdefault(name, []).append(params)

    if request.is_json:
        return jsonify(index_names)
    else:
        return render_template(
            'names.html',
            datachecks=index_names
        )


@app.route('/names/list', methods=['GET'])
def names_list():
    return jsonify(get_names_list())


@app.route('/groups/', methods=['GET'])
@app.route('/groups/<string:group_param>', methods=['GET'])
def groups(group_param=None):
    index_groups = {}
    if not app.index:
        # Empty list of compara
        raise MissingIndexException

    for name, params in app.index.items():
        for group in params['groups']:
            if group_param is None or group == group_param:
                index_groups.setdefault(group, []).append(params)

    if request.is_json:
        return jsonify(index_groups)
    else:
        return render_template(
            'groups.html',
            datachecks=index_groups
        )


@app.route('/groups/list', methods=['GET'])
def groups_list():
    return jsonify(get_groups_list())


@app.route('/types/', methods=['GET'])
@app.route('/types/<string:type_param>', methods=['GET'])
def types(type_param=None):
    index_types = {}
    if not app.index:
        # Empty list of compara
        raise MissingIndexException

    for name, params in app.index.items():
        if type_param is None or params['datacheck_type'] == type_param:
            index_types.setdefault(params['datacheck_type'], []).append(params)

    if request.is_json:
        return jsonify(index_types)
    else:
        return render_template(
            'types.html',
            datachecks=index_types
        )


@app.route('/search/<string:keyword>', methods=['GET'])
def search(keyword):
    index_search = {}
    keyword_re = re.compile(keyword, re.IGNORECASE)

    for name, params in app.index.items():
        if keyword_re.search(name) or keyword_re.search(params['description']):
            index_search.setdefault(keyword, []).append(params)
    return jsonify(index_search)


@app.route('/dropdown/databases/<string:src_host>/<string:src_port>', methods=['GET'])
def dropdown(src_host=None, src_port=None):
    try:
        search = request.args.get('search', None)
        if src_host and src_port and search:
            res = requests.get(f"{DatacheckConfig.COPY_URI_DROPDOWN}api/dbcopy/databases/{src_host}/{src_port}",
                               params={'search': search})
            res.raise_for_status()
            return jsonify(res.json())
        else:
            raise Exception('required params not provided')
    except HTTPError as http_err:
        raise HTTPRequestError(f'{http_err}', 404)
    except Exception as e:
        print(str(e))
        return jsonify([])


@app.route('/jobs', methods=['POST'])
def job_submit(payload=None):
    # Most of the parameters that are in the payload can be pushed straight
    # through to the input_data for the hive submission. The parameter names
    # have been made to match up nicely. However, there are a few input
    # parameters that need to be derived from the payload ones.
    if payload is None:
        payload = request.json

    input_data = dict(payload)
    app.logger.info('Received payload %s', input_data)
    assert_mysql_uri(input_data['server_url'])

    if 'target_url' in input_data:
        input_data['server_uri'] = input_data['target_url'].split(',')

    # Determine db_type if necessary.
    # Convert all species-selection parameters to lists, as required by the hive pipeline
    dbname = input_data['dbname']
    if dbname is not None:
        db_uri = input_data['server_url'] + dbname
        assert_mysql_db_uri(db_uri)
        input_data['db_type'] = set_db_type(dbname, db_uri)
        input_data['dbname'] = dbname.split(',')
    elif input_data['species'] is not None:
        input_data['species'] = input_data['species'].split(',')
    elif input_data['division'] is not None:
        input_data['division'] = input_data['division'].split(',')

    # Hard-code this for the time being; need to handle memory usage better for unparallelised runs
    input_data['parallelize_datachecks'] = 1

    servers = get_servers_dict()
    app.logger.info('Servers %s', servers)
    server_name = servers[input_data['server_url']]['server_name']
    config_profile = servers[input_data['server_url']]['config_profile']
    if dbname is not None:
        if is_grch37(dbname):
            config_profile = 'grch37'

    input_data['registry_file'] = set_registry_file(server_name)

    input_data['config_file'] = set_config_file(config_profile)
    app.logger.info('get Hive %s', get_hive())
    job = get_hive().create_job(app.analysis, input_data)
    app.logger.info("Job created %s", job)
    if request.is_json:
        results = {"job_id": job.job_id}
        return jsonify(results), 201
    else:
        return redirect('/jobs/' + str(job.job_id))


@app.route('/jobs', methods=['GET'])
def job_list():
    if not app.index:
        # Empty list DC
        raise MissingIndexException

    fmt = request.args.get('format', None)
    job_id = request.args.get('job_id', None)

    if request.is_json or fmt == 'json':
        if job_id:
            jobs = [get_hive().get_result_for_job_id(job_id, progress=True)]
        else:
            jobs = get_hive().get_all_results(app.analysis)
            # Handle case where submission is marked as complete,
        # but where output has not been created.
        for job in jobs:
            if 'output' not in job.keys():
                job['status'] = 'incomplete'
            elif job['output']['failed_total'] > 0:
                job['status'] = 'failed'

        return jsonify(jobs)

    return render_template('list.html', job_id=job_id)


@app.route('/jobs/details', methods=['GET'])
def job_details():
    try:
        jsonfile = request.args.get('jsonfile', None)
        file_data = open(jsonfile, 'r').read()
        return jsonify(json.loads(file_data))
    except Exception:
        return jsonify({'Could not retrieve results'})


@app.route('/jobs/<int:job_id>', methods=['GET'])
def job_result(job_id):
    job = get_hive().get_result_for_job_id(job_id, progress=True)
    fmt = request.args.get('format', None)
    # Handle case where submission is marked as complete,
    # but where output has not been created.
    if 'output' not in job.keys():
        job['status'] = 'incomplete'
    elif job['output']['failed_total'] > 0:
        job['status'] = 'failed'
    elif job['output']['passed_total'] == 0:
        job['status'] = 'failed'

    if request.is_json or fmt == 'json':
        return jsonify(job)
    else:
        # Need to pass some data to the template...
        return render_template('list.html', job_id=job_id)


@app.route('/download_datacheck_outputs/<int:job_id>')
def download_dc_outputs(job_id):
    job = get_hive().get_result_for_job_id(job_id, progress=False)
    if 'output' in job:
        base_path = Path(job['output']['output_dir'])
        paths = list(base_path.iterdir())
        if len(paths) > 1:
            data = BytesIO()
            with ZipFile(data, mode='w') as z:
                for f_path in paths:
                    z.write(str(f_path), f_path.name)
            data.seek(0)
            filename = 'Datacheck_output_job_%s.zip' % job_id
            return send_file(data, mimetype='application/zip',
                             attachment_filename=filename, as_attachment=True)
        else:
            for f_path in paths:
                return send_file(str(f_path), as_attachment=True)


@app.route('/jobs/submit', methods=['POST', 'GET'])
def display_form():
    # Here we convert the form fields into a 'payload' dictionary
    # that is the required input format for the hive submission.
    if not app.index:
        # Empty list DC
        raise MissingIndexException

    try:

        form = DatacheckSubmissionForm(request.form)
        server_name_choices = [('', '')]
        server_name_dict = {}

        for i, j in get_servers_dict().items():
            server_name_dict[j['server_name']] = i

        for name in sorted(server_name_dict):
            server_name_choices.append((server_name_dict[name], name))

        form.server.server_name.choices = server_name_choices

        if request.method == 'POST':

            if not form.validate():
                if form.server.source.data != 'division' and not any(
                        [form.server.dbname.data, form.server.species.data]):
                    form.server.dbname.errors = ['Database name or Species name required..!']
                raise Exception('Invalid Form ...')

            payload = {
                'server_url': form.server.server_name.data,
                'dbname': None,
                'species': None,
                'division': None,
                'db_type': None,
                'datacheck_names': [],
                'datacheck_groups': [],
                'datacheck_types': [],
                'email': form.submitter.email.data,
                'tag': form.submitter.tag.data
            }

            if form.server.source.data == 'dbname':
                payload['dbname'] = form.server.dbname.data
            else:
                if form.server.source.data == 'species':
                    payload['species'] = form.server.species.data
                elif form.server.source.data == 'division':
                    payload['division'] = form.server.division.data

                payload['db_type'] = form.server.db_type.data

            if form.datacheck.datacheck_name.data != '':
                payload['datacheck_names'] = form.datacheck.datacheck_name.data.split(',')
            if form.datacheck.datacheck_group.data != '':
                payload['datacheck_groups'] = form.datacheck.datacheck_group.data.split(',')
            if form.datacheck.datacheck_type.data != '':
                payload['datacheck_types'] = form.datacheck.datacheck_type.data.split(',')

            return job_submit(payload)

    except Exception as e:
        flash(str(e))

    return render_template(
        'submit.html',
        form=form,
    )


@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({'status': 'ok'})


def set_db_type(dbname, db_uri):
    p = re.compile('cdna|otherfeatures|rnaseq')
    m = p.search(dbname)
    if m is not None:
        db_type = m.group()
    else:
        db_type = get_db_type(db_uri)
    return db_type


def set_registry_file(server_name):
    return os.path.join(app.config['DATACHECK_REGISTRY_DIR'], '.'.join([server_name, 'pm']))


def set_config_file(config_profile):
    return os.path.join(app.config['DATACHECK_CONFIG_DIR'], '.'.join([config_profile, 'json']))


def is_grch37(dbname):
    p = re.compile('homo_sapiens.*_37')
    return p.match(dbname)


@app.errorhandler(HTTPRequestError)
def handle_bad_request_error(e):
    app.logger.error(str(e))
    return jsonify(error=str(e)), e.status_code


@app.errorhandler(404)
def handle_sqlalchemy_error(e):
    app.logger.error(str(e))
    return jsonify(error=str(e)), 404


@app.errorhandler(requests.exceptions.HTTPError)
def handle_server_error(e):
    return jsonify(error=str(e)), 500


@app.errorhandler(ensembl.production.datacheck.exceptions.MissingIndexException)
def handle_server_error(e):
    message = f"Missing Datacheck index configuration for {app.config['ENS_VERSION']} {e}"
    return jsonify(error=message), 500
