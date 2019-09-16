import os
import re
import time
from flask import Flask, json, jsonify, redirect, render_template, request
from flask_bootstrap import Bootstrap
from flask_cors import CORS
from flasgger import Swagger

from ensembl.datacheck.config import DatacheckConfig
from ensembl.forms import DatacheckSubmissionForm
from ensembl.hive import HiveInstance
from ensembl.db_utils import get_databases_list

# Go up two levels to get to root, where we will find the static and template files
app_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
static_path = os.path.join(app_path, 'static')
template_path = os.path.join(app_path, 'templates')

app = Flask(__name__, static_url_path='', static_folder=static_path, template_folder=template_path)

app.config.from_object(DatacheckConfig)

Bootstrap(app)

CORS(app)

Swagger(app, template_file='swagger.yml')


app.analysis = app.config['HIVE_ANALYSIS']
app.index = json.load(open(app.config['DATACHECK_INDEX']))
app.server_uris = json.load(open(os.path.join(app_path, app.config['SERVER_URIS_FILE'])))


app.names_list = []

def get_names_list():
  if not app.names_list:
    for name, params in app.index.items():
      app.names_list.append(name)
    app.names_list.sort()
  return app.names_list


app.groups_list = []

def get_groups_list():
  if not app.groups_list:
    groups_list = []
    for name, params in app.index.items():
      for group in params['groups']:
        groups_list.append(group)
    app.groups_list = sorted(set(groups_list))
  return app.groups_list


app.servers_list = []

def get_servers_list():
  if not app.servers_list:
    servers_list = app.server_uris
    app.servers_list = sorted(set(servers_list))
  return app.servers_list


hive = None

def get_hive(hive_server='vertebrates'):
  global hive
  if hive is None:
    if hive_server == 'vertebrates':
      hive = HiveInstance(app.config['HIVE_VERT_URI'])
    elif hive_server == 'non_vertebrates':
      hive = HiveInstance(app.config['HIVE_NONVERT_URI'])
    else:
      raise RuntimeError('Unrecognised Pipeline Server: %s' % hive_server)
  return hive


@app.route('/datacheck/', methods=['GET'])
def index():
  return render_template('ensembl/datacheck/index.html')


@app.route('/datacheck/servers/list', methods=['GET'])
def servers_list():
  return jsonify(get_servers_list())

@app.route('/datacheck/databases/list', methods=['GET'])
def databases_list():
  db_uri = request.args.get('db_uri')
  query = request.args.get('query')
  return jsonify(get_databases_list(db_uri, query))


@app.route('/datacheck/names/', methods=['GET'])
@app.route('/datacheck/names/<string:name_param>', methods=['GET'])
def names(name_param=None):
  if name_param is None:
    index_names = app.index
  else:
    index_names = {}
    for name, params in app.index.items():
      if name == name_param:
        index_names.setdefault(name,[]).append(params)

  if request.is_json:
    return jsonify(index_names)
  else:
    return render_template(
      'ensembl/datacheck/names.html',
      datachecks = index_names
    )

@app.route('/datacheck/names/list', methods=['GET'])
def names_list():
  return jsonify(get_names_list())


@app.route('/datacheck/groups/', methods=['GET'])
@app.route('/datacheck/groups/<string:group_param>', methods=['GET'])
def groups(group_param=None):
  index_groups = {}
  for name, params in app.index.items():
    for group in params['groups']:
      if group_param is None or group == group_param:
        index_groups.setdefault(group,[]).append(params)

  if request.is_json:
    return jsonify(index_groups)
  else:
    return render_template(
      'ensembl/datacheck/groups.html',
      datachecks = index_groups
    )

@app.route('/datacheck/groups/list', methods=['GET'])
def groups_list():
  return jsonify(get_groups_list())


@app.route('/datacheck/types/', methods=['GET'])
@app.route('/datacheck/types/<string:type_param>', methods=['GET'])
def types(type_param=None):
  index_types = {}
  for name, params in app.index.items():
    if type_param is None or params['datacheck_type'] == type_param:
      index_types.setdefault(params['datacheck_type'],[]).append(params)

  if request.is_json:
    return jsonify(index_types)
  else:
    return render_template(
      'ensembl/datacheck/types.html',
      datachecks = index_types
    )


@app.route('/datacheck/search/<string:keyword>', methods=['GET'])
def search(keyword):
  index_search = {}
  keyword_re = re.compile(keyword, re.IGNORECASE)

  for name, params in app.index.items():
    if keyword_re.search(name) or keyword_re.search(params['description']):
        index_search.setdefault(keyword,[]).append(params)

  return jsonify(index_search)


@app.route('/datacheck/jobs', methods=['POST'])
def job_submit(payload = None):
  # Most of the parameters that are in the payload can be pushed straight
  # through to the input_data for the hive submission. The parameter names
  # have been made to match up nicely. However, there are a few input
  # parameters that need to be derived from the payload ones, and once that's
  # done we remove them from the input dictionary.
  if payload is None:
    payload = request.json

  input_data = dict(payload)

  if payload['database']:
    input_data['run_all'] = 1

  # Hard-code this for the time being; need to handle memory usage better for unparallelised runs
  input_data['parallelize_datachecks'] = 1

  input_data['registry_file'] = set_registry_file(payload)

  input_data['config_file'] = set_config_file(payload)

  del input_data['server_url']
  del input_data['database']
  del input_data['release']
  del input_data['config_profile']

  print(input_data)

  hive_server = 'vertebrates'
  if payload['config_profile'] != 'vertebrates':
    hive_server = 'non_vertebrates'

  job = get_hive(hive_server).create_job(app.analysis, input_data)

  if request.is_json:
    results = {"job_id": job.job_id}
    return jsonify(results), 201
  else:
    return redirect('/datacheck/jobs/' + str(job.job_id))


@app.route('/datacheck/jobs', methods=['GET'])
def job_list():
  jobs = get_hive().get_all_results(app.analysis)
  
  # Handle case where submission is marked as complete,
  # but where output has not been created.
  for job in jobs:
    if job['status'] == 'complete' and 'output' not in job.keys():
      job['status'] = 'failed'

  #if request.is_json:
  return jsonify(jobs)
  #else:
    # Need to pass some data to the template...
    #return render_template('ensembl/datacheck/list.html')


@app.route('/datacheck/jobs/<int:job_id>', methods=['GET'])
def job_result(job_id):
  job = get_hive().get_result_for_job_id(job_id, progress=False)

  # Handle case where submission is marked as complete,
  # but where output has not been created.
  if job['status'] == 'complete' and 'output' not in job.keys():
    job['status'] = 'failed'

  #if request.is_json:
  return jsonify(job)
  #else:
    # Need to pass some data to the template...
    #return render_template('ensembl/datacheck/detail.html')


@app.route('/datacheck/submit', methods=['GET'])
def display_form():
  form = DatacheckSubmissionForm(request.form)

  return render_template(
    'ensembl/datacheck/submit.html',
    form = form
  )


@app.route('/datacheck/submit', methods=['POST'])
def submit_form():
  # Here we convert the form fields into a 'payload' dictionary
  # that is the required input format for the hive submission.

  form = DatacheckSubmissionForm(request.form)

  payload = {
    'server_url': form.server.server_url.data,
    'database': None,
    'species': None,
    'division': None,
    'db_type': None,
    'release': None,
    'datacheck_names':[],
    'datacheck_groups': [],
    'datacheck_types': [],
    'config_profile': form.configuration.config_profile.data,
    'email': form.configuration.email.data,
    'tag': form.configuration.tag.data
  }

  if form.server.source.data == 'database':
    payload['database'] = form.server.database.data
  else:
    if form.server.source.data == 'species':
      payload['species'] = form.server.species.data.split(',')
    elif form.server.source.data == 'division':
      payload['division'] = form.server.division.data.split(',')

    payload['db_type'] = form.server.database_type.data
    payload['release'] = dict(form.server.release.choices).get(form.server.release.data)

  if form.datacheck.datacheck_name.data != '':
    payload['datacheck_names'] = form.datacheck.datacheck_name.data.split(',')
  if form.datacheck.datacheck_group.data != '':
    payload['datacheck_groups'] = form.datacheck.datacheck_group.data.split(',')
  if form.datacheck.datacheck_type.data != '':
    payload['datacheck_types'] = form.datacheck.datacheck_type.data.split(',')

  return job_submit(payload)


@app.route('/datacheck/ping', methods=['GET'])
def ping():
  return jsonify({'status': 'ok'})


def set_registry_file(params):
  # We need to create a registry file that knows where the metadata and
  # production db are, because some datachecks need them; so we read those in from a file.
  # We then need to work out whether we're connecting to a specific database,
  # or a server with species/division parameters, and add the appropriate stanza.

  # Note that we don't need to check server_url format here,
  # both the client script and web page perform validation.

  meta_db_file = open(app.config['DATACHECK_REGISTRY_META'], 'r')
  meta_db_text = meta_db_file.read()
  meta_db_file.close()

  db_url = None
  if params['database']:
    if not params['db_type']:
      if 'compara' in params['database']:
        params['db_type'] = 'compara'
      else:
        m = re.match(r'.+\_([a-z]+)', params['database'])
        params['db_type'] = m.group(1)

      db_url = os.path.join(params['server_url'], params['database'], '?group=' + params['db_type'])
  elif params['species'] or params['division']:
    db_url = params['server_url']
    if params['release']:
      db_url = os.path.join(db_url, params['release'])

  timestamp = str(int(time.time()))
  registry_path = os.path.join(app.config['DATACHECK_REGISTRY_DIR'], '_'.join([timestamp, 'registry.pm']))

  registry_file = open(registry_path, 'x')
  registry_file.write(meta_db_text)
  registry_file.write("Bio::EnsEMBL::Registry->load_registry_from_url('" + db_url + "');\n")
  registry_file.write('1;\n')
  registry_file.close()

  return registry_path

def set_config_file(params):
  return os.path.join(app.config['DATACHECK_CONFIG_DIR'], '.'.join([params['config_profile'], 'json']))
