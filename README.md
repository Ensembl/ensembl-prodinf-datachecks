# README
Overview
========

The Datacheck service provides a set of endpoints to allow Datacheck to be run on specified Ensembl MySQL databases. 

Implementation
==============

The `datacheck app <./src/ensembl/production/datacheck/app/main.py>`_ is a simple Flask app which defines endpoints for datacheck. After starting the app, full API documentation is available from ``/apidocs``.



Installation
============

Create directory  datacheck_app
```
mkdir datacheck_app
cd datacheck_app
```
Clone the necessary repositories:
```
git clone https://github.com/Ensembl/ensembl
git clone https://github.com/Ensembl/ensembl-hive
git clone https://github.com/Ensembl/ensembl-datacheck.git
git clone https://github.com/Ensembl/ensembl-compara
git clone https://github.com/Ensembl/ensembl-funcgen
git clone https://github.com/Ensembl/ensembl-metadata
git clone https://github.com/Ensembl/ensembl-orm
git clone https://github.com/Ensembl/ensembl-variation
git clone https://github.com/Ensembl/ensembl-prodinf-datachecks.git
```

To install Python requirements using pip:

``` 
  cd ensembl-prodinf-datachecks
  pip install -r requirements.txt
  pip install .    
```

Configuration
=============
## Hive configuration
The datacheck service uses the
[DbDataChecks_conf.pm](https://github.com/Ensembl/ensembl-datacheck/tree/master/lib/Bio/EnsEMBL/DataCheck/Pipeline/DbDataChecks_conf.pm)
hive pipeline to perform the necessary updates.

    SRV=h1-w # Or the MySQL command shortcut for another server
    init_pipeline.pl lib/Bio/EnsEMBL/DataCheck/Pipeline/DbDataChecks_conf.pm $($SRV details hive)

Start the beekeeper with the `--loop_until FOREVER` parameter.

## App configuration
Export environment variables required by datacheck app

    DATACHECK_COMMON_DIR='<path>'
    HIVE_ANALYSIS='DataCheckSubmission'
    HIVE_URI='mysql://user:pass@mysqlhost:3366/'ensprod_db_datachecks_production'
    SERVER_NAMES_FILE='server_names_file'
    COPY_URI_DROPDOWN="http://production-services.ensembl.org:80/"



Alternatively, a yaml file can be used to provide the uris:

    export DATACHECK_CONFIG_PATH=/<path>/config.yaml

    example for config.yaml contains:
    -------------------------
    base_dir: '/home/appuser/'
    datacheck_output_dir: '/nfs/nobackup/'
    datacheck_common_dir: '/nfs/panda/'
    hive_uri: 'mysql://user:pass@mysqlhost:3366/'ensprod_db_datachecks_production'
    server_names_file: '/home/appuser/server_names.json'
    swagger_file: '/home/appuser/swagger.yml'


Running
=======

To start the main application as a standalone Flask application:

```
  export FLASK_APP=ensembl.production.datacheck.app.main.py
  flask run --port 5003 --host 0.0.0.0
```
or to start the main application as a standalone using gunicorn with 4 threads:

```
  gunicorn -w 4 -b 0.0.0.0:5003 ensembl.production.datacheck.app.main:app
```
Note that for production, a different deployment option should be used as the standalone flask app can only serve one request at a time.

There are multiple options, described at:
```
* http://flask.pocoo.org/docs/0.12/deploying/wsgi-standalone/
* http://flask.pocoo.org/docs/0.12/deploying/uwsgi/
```
To use a standalone gunicorn server with 4 worker threads:

```
  gunicorn -w 4 -b 0.0.0.0:5001 datacheck_app:app
```


Build Docker Image 
==================
```
sudo docker build -t datacheck . 
```

RUN Docker Container
====================
```
sudo docker run -p 5000:5000 -it  datacheck:latest
```



