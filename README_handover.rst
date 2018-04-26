Installation
============

To install Python requirements using pip:

.. code-block:: bash

  pip install -r requirements.txt

This will install ``ensembl_prodinf`` from git - alternatively to reference an existing install to PYTHONPATH e.g.

.. code-block:: bash

  PYTHONPATH=dir/ensembl-prodinf/ensembl-prodinf-core


Configuration
=============

There are two configuration files you need to have copies of locally:

.. code-block:: bash

  mkdir instance
  cp handover_config.py.instance_example instance/handover_config.py
  cp handover_celery_app_config.py.example handover_celery_app_config.py

Running
=======

To start the main application as a standalone Flask application:

.. code-block:: bash

  export FLASK_APP=handover_app.py
  flask run --port 5003 --host 0.0.0.0

or to start the main application as a standalone using gunicorn with 4 threads:

.. code-block:: bash

  pyenv activate ensprod_inf
  gunicorn -w 4 -b 0.0.0.0:5003 handover_app:app

Note that for production, a different deployment option should be used as the standalone flask app can only serve one request at a time.

There are multiple options, described at:

* http://flask.pocoo.org/docs/0.12/deploying/wsgi-standalone/
* http://flask.pocoo.org/docs/0.12/deploying/uwsgi/

To use a standalone gunicorn server with 4 worker threads:

.. code-block:: bash

  gunicorn -w 4 -b 0.0.0.0:5001 handover_app:app

Running Celery
==============
The Celery task manager is currently used for coordinating handover jobs. The default backend in ``handover_celery_app_config.py`` is RabbitMQ. This can be installed as per https://www.rabbitmq.com/ rabbitmq_server-3.6.10 has been successfully installed from tarball (assuming erlang is already installed).

To start a celery worker to handle handover:

.. code-block:: bash

  pyenv activate ensprod_inf
  celery -A ensembl_prodinf.handover_tasks worker -l info -Q handover -n handover@%h
