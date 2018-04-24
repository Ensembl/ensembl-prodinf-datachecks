Installation
============

To install Python requirements using pip:
```
pip install -r requirements.txt
```

You can do this on a shared pyenv environment, or per user with the `--user` option.

You can also install `ensembl_prodinf` from git or by adding an existing install to PYTHONPATH.
e.g: PYTHONPATH=dir/ensembl-prodinf/ensembl-prodinf-core

Hive Setup
==========

Before you can use the HC endpoint, you need a beekeeper running the pipeline defined by `Bio::EnsEMBL::Healthcheck::Pipeline::RunStandaloneHealthchecksParallel_conf`. This also needs a Java jar. To build and initiate the pipeline:
```
git clone https://github.com/Ensembl/ensj-healthcheck
cd ensj-healthcheck
mvn clean package
JAR=$PWD/target/healthchecks-jar-with-dependencies.jar
SRV=your_mysql_command_wrapper
init_pipeline.pl Bio::EnsEMBL::Healthcheck::Pipeline::RunStandaloneHealthchecksParallel_conf $($SRV details hive) -hc_jar $JAR 
```

Next, run the `beekeeper.pl` supplied by the output with the arguments `--keep_alive -sleep 0.5`. This ensures the hive runs continually, picking up new jobs as they are submitted.

Configuration
=============

There are two configuration files you need to have copies of locally:
```
mkdir instance
cp hc_config.py.instance_example instance/hc_config.py
cp celery_app_config.py.example celery_app_config.py
```

Edit them as required. hc_config.py must contain a URL for the hive MySQL instance described above.

You can also leave instance/hc_config.py empty and use the defaults in hc_config.py or override using environment variables.

The following environment variables are supported by the container:
* HIVE_URI - mysql URI of HC hive database (required)
* HIVE_ANALYSIS - name of analysis for submitting new jobs to the hive (not usually needed to be changed)
* CELERY_BROKER_URL - URL of Celery broker
* CELERY_RESULT_BACKEND - URl of Celery backend

Running Celery
==============
The Celery task manager is currently used for scheduling checks on completed jobs. The default backend in celery_app_config.py is RabbitMQ. This can be installed as per https://www.rabbitmq.com/ rabbitmq_server-3.6.10 has been successfully installed from tarball (assuming erlang is already installed).

To start a celery worker to handle email:
```
celery -A ensembl_prodinf.email_tasks worker -l info
```


Running
=======

To start the main application as a standalone Flask application:
```
export FLASK_APP=hc_app.py
cd ensembl-prodinf-srv
flask run --port 5001 --host 0.0.0.0
```
or to start the main application as a standalone using gunicorn with 4 threads:
```
pyenv activate ensprod_inf
cd ensembl-prodinf-srv
gunicorn -w 4 -b 0.0.0.0:5001 hc_app:app
```

Note that for production, a different deployment option should be used as the standalone flask app can only serve one request at a time.

There are multiple options, described at:
* http://flask.pocoo.org/docs/0.12/deploying/wsgi-standalone/
* http://flask.pocoo.org/docs/0.12/deploying/uwsgi/

To use a standalone gunicorn server with 4 worker threads:
```
gunicorn -w 4 -b 0.0.0.0:5001 hc_app:app
```

Using Docker
============

To build a Docker image:
```
docker build -t ensembl_prodinf/hc_app -f Dockerfile.hc .
```

To run your Docker image against a specified hive, exposing the REST service on port 4001 e.g.:
```
docker run -p 127.0.0.1:4001:4001 --env HIVE_URI='mysql://user:pwd@localhost:3306/my_hive_db' ensembl_prodinf/hc_app
```

Environment variables should be supplied as arguments to the run command as shown in the example above.
