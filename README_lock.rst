Installation
============

To install Python requirements using pip:
```
pip install -r requirements.txt
```

You can do this on a shared pyenv environment, or per user with the `--user` option.

You can also install `ensembl_prodinf` from git or by adding an existing install to PYTHONPATH.
e.g: PYTHONPATH=dir/ensembl-prodinf/ensembl-prodinf-core

Database Setup
==============

Before you can use the lock endpoint, you need to create an empty schema for the resource locks to be stored in. Any tables needed will be automatically created.

Configuration
=============

Configuration is via the config file `lock_config.py`. The only configuration property is LOCK_URI which should be the URI for the lock database (see above). You can also set this as an environment variable.

Running
=======

To start the main application as a standalone Flask application:
```
export FLASK_APP=lock_app.py
cd ensembl-prodinf-srv
flask run --port 5001 --host 0.0.0.0
```
or to start the main application as a standalone using gunicorn with 4 threads:
```
pyenv activate ensprod_inf
cd ensembl-prodinf-srv
gunicorn -w 4 -b 0.0.0.0:5001 lock_app:app
```

Note that for production, a different deployment option should be used as the standalone flask app can only serve one request at a time.

There are multiple options, described at:
* http://flask.pocoo.org/docs/0.12/deploying/wsgi-standalone/
* http://flask.pocoo.org/docs/0.12/deploying/uwsgi/

To use a standalone gunicorn server with 4 worker threads:
```
gunicorn -w 4 -b 0.0.0.0:5001 lock_app:app
```

Using Docker
============

To build a Docker image:
```
docker build -t ensembl_prodinf/lock_app -f Dockerfile.hc .
```

To run your Docker image against a specified hive, exposing the REST service on port 4001 e.g.:
```
docker run -p 127.0.0.1:4001:4001 --env LOCK_URI='mysql://user:pwd@myhost:3306/my_hive_db' ensembl_prodinf/lock_app
```

Environment variables should be supplied as arguments to the run command as shown in the example above.
