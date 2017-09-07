Overview
========

This project contains the following Python web applications (written using the Flask framework):
* db_app - a set of endpoints for interacting with MySQL database servers
* hc_app - a set of endpoints for executing Ensembl healtchecks

Installation
============

To install Python requirements using pip:
```
pip install -r requirements.txt
```

Configuration
=============

There are two configuration files you need to have copies of locally:
```
mkdir instance
cp hc_config.py.instance_example instance/hc_config.py
cp celery_app_config.py.example celery_app_config.py
```

Edit them as required.

Running
=======

For email feedback to work, the celery backend specified in celery_app_config.py needs to be available.

The default configuration uses RabbitMQ, which should be installed and started as described in https://www.rabbitmq.com/

To start the main application as a standalone Flask application:
For the HC server:
```
export FLASK_APP=hc_app.py
flask run --port 5001
```

For the DB server:
```
export FLASK_APP=db_app.py
flask run --port 5002
```

Note that for production, a different deployment option should be used as the standalone flask app can only serve one request at a time.
