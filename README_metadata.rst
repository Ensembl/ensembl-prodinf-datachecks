Installation
============

To install Python requirements using pip:
```
pip install -r requirements.txt
```
You can also install `ensembl_prodinf` from git or by adding an existing install to PYTHONPATH.
e.g: PYTHONPATH=dir/ensembl-prodinf/ensembl-prodinf-core

Hive Setup
==========

Before you can use the HC endpoint, you need a beekeeper running the pipeline defined by `Bio::EnsEMBL::Production::Pipeline::PipeConfig::CopyDatabase_conf`. To build and initiate the pipeline:
```
git clone https://github.com/Ensembl/ensembl-metadata
cd ensembl-metadata
SRV=your_mysql_command_wrapper from where your hive will be running.
init_pipeline.pl Bio::EnsEMBL::MetaData::Pipeline::MetadataUpdater_conf $($SRV details hive)
```

Next, run the `beekeeper.pl` supplied by the output with the arguments `--keep_alive -sleep 0.5`. This ensures the hive runs continually, picking up new jobs as they are submitted.

Configuration
=============
There are two configuration files you need to have copies of locally. 
```
cp celery_app_config.py.example celery_app_config.py
```

Secondly, you can provide an instance file, the location of which depends if you're using virtualenv or not.

For virtualenv:
```
mkdir -p vars/metadata_app-instance
cp metadata_config.py.instance_example vars/metadata_app-instance/metadata_config.py 
```

Otherwise:
```
mkdir instance
cp metadata_config.py.instance_example instance/metadata_config.py 
```

Edit them as required. SERVER_URIS_FILE must point to a JSON file containing lists of server names for autocomplete e.g.
```
SERVER_URIS_FILE = 'server_uris.json'
HIVE_URI='mysql://myuser:mypass@myhost:3306/metadata_updater'
```
An example can be found in `server_uris.json.example`.

Note that you can leave instance files empty, and use the defaults found in metadata_config.py, or override them at run time with environment variables.

The following environment variables are supported:
* SERVER_URIS_FILE - path to JSON file containing server details
* HIVE_URI - mysql URI of DB copy hive database
* HIVE_ANALYSIS - name of analysis for submitting new jobs to the hive (not usually needed to be changed)
* CELERY_BROKER_URL - URL of Celery broker
* CELERY_RESULT_BACKEND - URL of Celery backend

Running
=======

To start the main application as a standalone Flask application:
```
export FLASK_APP=metadata_app.py
cd ensembl-prodinf-srv
flask run --port 5003 --host 0.0.0.0
```
or to start the main application as a standalone using gunicorn with 4 threads:
```
pyenv activate ensprod_inf
cd ensembl-prodinf-srv
gunicorn -w 4 -b 0.0.0.0:5003 metadata_app:app
```

Note that for production, a different deployment option should be used as the standalone flask app can only serve one request at a time.

Using Docker
============

To build a Docker image, first copy `ssh_config.example` to `ssh_config` and make any changes required (e.g. path to ssh keys) and then build:
```
docker build -t ensembl_prodinf/metadata_app -f Dockerfile.metadata .
```
Supported environment variables (see above) should be supplied as arguments to the run command as shown in the example above.

The database status endpoint relies on certificate-based SSH to other machines, so the container needs access to the identity files specified in the ssh_config file. For the example file provided, you must mount a directory containing `id_rsa` and `id_rsa.pub` using the path specified in the `ssh_config` file using the `--mount` argument.

In addition, the file specified in `SERVER_URIS` must also be available. Again, this can be provided with an additional volume using the `--mount` argument.

To run your Docker image against a specified hive, exposing the REST service on port 4002 e.g.:
```
docker run -p 127.0.0.1:4002:4002 \
       --mount type=bind,src=$PWD/ssh_keys/,target=/ssh_keys/ \
       --mount type=bind,src=$PWD/server_uris/,target=/server_uris \
       --env HIVE_URI='mysql://user:pwd@localhost:3306/my_hive_db' \
       --env SERVER_URIS_FILE='/server_uris/server_uris.json' \
       ensembl_prodinf/metadata_app
```
