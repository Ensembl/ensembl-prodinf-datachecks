import os
from flask import Flask, flash, json, jsonify, redirect, render_template, request, url_for
from flask_bootstrap import Bootstrap
from flask_cors import CORS
from flasgger import Swagger

from ensembl.gifts.config import GIFTsConfig
from ensembl.forms import GIFTsSubmissionForm
from ensembl.hive import HiveInstance

# Go up two levels to get to root, where we will find the static and template files
app_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
static_path = os.path.join(app_path, 'static')
template_path = os.path.join(app_path, 'templates')

app = Flask(__name__, static_url_path='', static_folder=static_path, template_folder=template_path)

app.config.from_object(GIFTsConfig)

Bootstrap(app)

CORS(app)

Swagger(app, template_file='swagger.yml')

hive = None

def get_gifts_api_uri(environment):
  with open(app.config["GIFTS_API_URIS_FILE"], 'r') as f:
    gifts_api_uris = json.loads(f.read())
    if environment in gifts_api_uris.keys():
      gifts_api_uri = gifts_api_uris[environment]
    else:
      raise RuntimeError('Unrecognised Environment: %s' % environment)
  return gifts_api_uri

def get_hive(hive_type):
  global hive
  if hive is None:
    if hive_type == 'update_ensembl':
      hive = HiveInstance(app.config["HIVE_UPDATE_ENSEMBL_URI"])
    elif hive_type == 'process_mapping':
      hive = HiveInstance(app.config["HIVE_PROCESS_MAPPING_URI"])
    elif hive_type == 'publish_mapping':
      hive = HiveInstance(app.config["HIVE_PUBLISH_MAPPING_URI"])
    else:
      raise RuntimeError('Unrecognised Pipeline: %s' % hive_type)
  return hive

@app.route('/gifts/', methods=['GET'])
def index():
  return render_template('ensembl/gifts/index.html')

@app.route('/gifts/update_ensembl', methods=['POST'])
@app.route('/gifts/update_ensembl/jobs', methods=['POST'])
def update_ensembl(payload=None):
  # call /gifts/update_ensembl/status to check that there are no active jobs before proceeding
  if payload is None:
    payload = request.json

  payload['rest_server'] = get_gifts_api_uri(payload['environment'])

  analysis = app.config['HIVE_UPDATE_ENSEMBL_ANALYSIS']
  job = get_hive('update_ensembl').create_job(analysis, payload)

  if request.is_json:
    results = {"job_id": job.job_id}
    return jsonify(results)
  else:
    return redirect(url_for('update_ensembl_result', job_id = str(job.job_id)))

@app.route('/gifts/update_ensembl', methods=['GET'])
@app.route('/gifts/update_ensembl/jobs', methods=['GET'])
def update_ensembl_list():
  analysis = app.config['HIVE_UPDATE_ENSEMBL_ANALYSIS']
  jobs = get_hive('update_ensembl').get_all_results(analysis)

  if request.is_json:
    return jsonify(jobs)
  else:
    return render_template('ensembl/gifts/list.html', submission_type='Update Ensembl', jobs=jobs)

@app.route('/gifts/update_ensembl/<int:job_id>', methods=['GET'])
@app.route('/gifts/update_ensembl/jobs/<int:job_id>', methods=['GET'])
def update_ensembl_result(job_id):
  job = get_hive('update_ensembl').get_result_for_job_id(job_id, progress=False)
  print(job)
  if request.is_json:
    return jsonify(job)
  else:
    return render_template('ensembl/gifts/detail.html', submission_type='Update Ensembl', job=job)

@app.route('/gifts/update_ensembl/status/<int:ensembl_release>', methods=['GET'])
def update_ensembl_status():
  analysis = app.config['HIVE_UPDATE_ENSEMBL_ANALYSIS']
  # get_hive('update_ensembl').get_all_results(analysis)
  # => work out latest job submission, then fetch its status, filtering on ensembl_release
  status = None

  return jsonify(status)

@app.route('/gifts/process_mapping', methods=['POST'])
@app.route('/gifts/process_mapping/jobs', methods=['POST'])
def process_mapping(payload=None):
  if payload is None:
    payload = request.json

  analysis = app.config['HIVE_PROCESS_MAPPING_ANALYSIS']
  job = get_hive('process_mapping').create_job(analysis, payload)

  if request.is_json:
    results = {"job_id": job.job_id}
    return jsonify(results)
  else:
    return redirect('/gifts/process_mapping/jobs/' + str(job.job_id))

@app.route('/gifts/process_mapping', methods=['GET'])
@app.route('/gifts/process_mapping/jobs', methods=['GET'])
def process_mapping_list():
  analysis = app.config['HIVE_PROCESS_MAPPING_ANALYSIS']
  jobs = get_hive('process_mapping').get_all_results(analysis)

  if request.is_json:
    return jsonify(jobs)
  else:
    return render_template('ensembl/gifts/list.html', submission_type='Process Mapping', jobs=jobs)

@app.route('/gifts/process_mapping/<int:job_id>', methods=['GET'])
@app.route('/gifts/process_mapping/jobs/<int:job_id>', methods=['GET'])
def process_mapping_result(job_id):
  job = get_hive('process_mapping').get_result_for_job_id(job_id, progress=False)

  if request.is_json:
    return jsonify(job)
  else:
    return render_template('ensembl/gifts/detail.html', submission_type='Process Mapping', job=job)

@app.route('/gifts/process_mapping/status/<int:ensembl_release>', methods=['GET'])
def process_mapping_status():
  analysis = app.config['HIVE_PROCESS_MAPPING_ANALYSIS']
  # get_hive('process_mapping').get_all_results(analysis)
  # => work out latest job submission, then fetch its status, filtering on ensembl_release
  status = None

  return jsonify(status)

@app.route('/gifts/publish_mapping', methods=['POST'])
@app.route('/gifts/publish_mapping/jobs', methods=['POST'])
def publish_mapping(payload=None):
  if payload is None:
    payload = request.json

  analysis = app.config['HIVE_PUBLISH_MAPPING_ANALYSIS']
  job = get_hive('publish_mapping').create_job(analysis, payload)

  if request.is_json:
    results = {"job_id": job.job_id}
    return jsonify(results)
  else:
    return redirect('/gifts/publish_mapping/jobs/' + str(job.job_id))

@app.route('/gifts/publish_mapping', methods=['GET'])
@app.route('/gifts/publish_mapping/jobs', methods=['GET'])
def publish_mapping_list():
  analysis = app.config['HIVE_PUBLISH_MAPPING_ANALYSIS']
  jobs = get_hive('publish_mapping').get_all_results(analysis)

  if request.is_json:
    return jsonify(jobs)
  else:
    return render_template('ensembl/gifts/list.html', submission_type='Publish Mapping', jobs=jobs)

@app.route('/gifts/publish_mapping/<int:job_id>', methods=['GET'])
@app.route('/gifts/publish_mapping/jobs/<int:job_id>', methods=['GET'])
def publish_mapping_result(job_id):
  job = get_hive('publish_mapping').get_result_for_job_id(job_id, progress=False)

  if request.is_json:
    return jsonify(job)
  else:
    return render_template('ensembl/gifts/detail.html', submission_type='Publish Mapping', job=job)

@app.route('/gifts/publish_mapping/status/<int:ensembl_release>', methods=['GET'])
def publish_mapping_status():
  analysis = app.config['HIVE_PUBLISH_MAPPING_ANALYSIS']
  # get_hive('publish_mapping').get_all_results(analysis)
  # => work out latest job submission, then fetch its status, filtering on ensembl_release
  status = None

  return jsonify(status)

@app.route('/gifts/submit', methods=['GET'])
def display_form():
  form = GIFTsSubmissionForm(request.form)

  return render_template(
    'ensembl/gifts/submit.html',
    form=form
  )

@app.route('/gifts/submit', methods=['POST'])
def submit_form():
  # Here we convert the form fields into a 'payload' dictionary
  # that is the required input format for the hive submission.
  form = GIFTsSubmissionForm(request.form)

  payload = {
    'ensembl_release': form.ensembl_release.data,
    'environment': form.environment.data,
    'email': form.email.data,
    'tag': form.tag.data
  }

  if form.update_ensembl.data:
    return update_ensembl(payload)
  elif form.process_mapping.data:
    return process_mapping(payload)
  elif form.publish_mapping.data:
    return publish_mapping(payload)
  else:
    raise RuntimeError('Unrecognised submission type')

@app.route('/gifts/ping', methods=['GET'])
def ping():
  return jsonify({'status': 'ok'})
