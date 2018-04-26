Overview
========

The event app provides a simple endpoint to initiate further processing in response to events on the staging server. Events in this case refer to events recorded in the `ensembl_metadata <https://github.com/Ensembl/ensembl-metadata>`_ database in response to change. It can be used programmatically from other pipelines, or manually when specific events need to be triggered. For more details, please see `event_processing.rst <https://github.com/Ensembl/ensembl-prodinf-core/blob/master/docs/event_processing.rst>`_

Implementation
==============

The `event app <./event_app.py>`_ is a simple Flask app which defines endpoints for event processing. After starting the app, full API documentation is available from ``/apidocs``.

The endpoints are defined in `hc_app.py <hc_app.py>`_ flask app. They use the
`ensembl-prodinf-core <https://github.com/Ensembl/ensembl-prodinf-core>`_ libraries for scheduling and monitoring Hive jobs. The endpoints consult lookup lists to determine which jobs need to be submitted to specified hives and analyses, if any, and submit jobs as required.

The submission of a event job also triggers the submission of a `celery <https://github.com/Ensembl/ensembl-prodinf-core/blob/master/docs/celery.rst>`_ task (`event_database <https://github.com/Ensembl/ensembl-prodinf-core/blob/master/ensembl_prodinf/event_tasks.py>`_) which coordinates the necessary processes for monitoring and further processing processes that .

Installation
============

To install Python requirements using pip:

.. code-block:: bash

  pip install -r requirements.txt

This will install ``ensembl_prodinf`` from git - alternatively to reference an existing install to ``PYTHONPATH`` e.g.

.. code-block:: bash

  PYTHONPATH=dir/ensembl-prodinf/ensembl-prodinf-core

Configuration
=============

There are two configuration files you need to have copies of locally:

.. code-block:: bash

  mkdir instance
  # this provides a local file-based override for values if required
  cp event_config.py.instance_example instance/event_config.py
  # this provides a details for
  cp event_celery_app_config.py.example event_celery_app_config.py

``event_config.py`` has the following values (these can be set by environment variables as well):

* ``EVENT_LOOKUP`` - JSON file mapping from events to processes
* ``PROCESS_LOOKUP`` - JSON file mapping from processes to hive analyses
* ``REPORT_SERVER`` - rabbitMQ server to send reports to
* ``REPORT_EXCHANGE`` - rabbitMQ exchange to send reports to
* ``EVENT_URI`` - URI of running event server (used for secondary submission of events)

The JSON files `process_lookup.json <./process_lookup.json>`_ and `event_lookup.json <./event_lookup.json>`_ are the default definitions used by the event processor to determine how to handle particular event classes.

Running
=======

To start the main application as a standalone Flask application:

.. code-block:: bash

  export FLASK_APP=event_app.py
  flask run --port 5003 --host 0.0.0.0

or to start the main application as a standalone using gunicorn with 4 threads:

.. code-block:: bash

  pyenv activate ensprod_inf
  gunicorn -w 4 -b 0.0.0.0:5003 event_app:app

Note that for production, a different deployment option should be used as the standalone flask app can only serve one request at a time.

There are multiple options, described at:

* http://flask.pocoo.org/docs/0.12/deploying/wsgi-standalone/
* http://flask.pocoo.org/docs/0.12/deploying/uwsgi/

To use a standalone gunicorn server with 4 worker threads:

.. code-block:: bash

  gunicorn -w 4 -b 0.0.0.0:5001 event_app:app

Running Celery
==============
The Celery task manager is currently used for coordinating event processing jobs. The default backend in ``event_celery_app_config.py`` is RabbitMQ. This can be installed as per <https://www.rabbitmq.com/>.

To start a celery worker to handle event jobs:

.. code-block:: bash

  pyenv activate ensprod_inf
  celery -A ensembl_prodinf.event_tasks worker -l info -Q event -n event@%h


Client
======

A simple Python REST client for this app can be found in `event_client.py <https://github.com/Ensembl/ensembl-prodinf-core/blob/master/ensembl_prodinf/event_client.py>`_.
