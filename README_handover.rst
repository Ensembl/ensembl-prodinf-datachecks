Overview
========

The handover app provides a simple endpoint to submit a new database to be checked and copied to the staging server for further automated processing. For more details, please see `handover.rst <https://github.com/Ensembl/ensembl-prodinf-core/blob/master/docs/handover.rst>`_

Implementation
==============

The `handover app <./handover_app.py>`_ is a simple Flask app which defines endpoints for handover. After starting the app, full API documentation is available from ``/apidocs``.

The submission of a handover job triggers the submission of a `celery <https://github.com/Ensembl/ensembl-prodinf-core/blob/master/docs/celery.rst>`_ task (`handover_database <https://github.com/Ensembl/ensembl-prodinf-core/blob/master/ensembl_prodinf/handover_tasks.py>`_) which coordinates the necessary processes for checking and importing a database.

Installation
============

First clone this repo

.. code-block:: bash

  git clone https://github.com/Ensembl/ensembl-prodinf-srv
  cd ensembl-prodinf-srv

To install Python requirements using pip:

.. code-block:: bash

  pip install -r requirements.txt

This will install ``ensembl_prodinf`` from git - alternatively to reference an existing install to ``PYTHONPATH`` e.g.

.. code-block:: bash

  PYTHONPATH=[install_dir]/ensembl-prodinf/ensembl-prodinf-core


Configuration
=============

Configuration is minimal and restricted to the contents of `handover_config.py <./handover_config.py>`_ which is restricted solely to basic Flask properties.

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
The Celery task manager is currently used for coordinating handover jobs. The default backend in ``handover_celery_app_config.py`` is RabbitMQ. This can be installed as per <https://www.rabbitmq.com/>.

To start a celery worker to handle handover:

.. code-block:: bash

  pyenv activate ensprod_inf
  celery -A ensembl_prodinf.handover_tasks worker -l info -Q handover -n handover@%h


Client
======

A simple Python REST client for this app can be found in `handover_client.py <https://github.com/Ensembl/ensembl-prodinf-core/blob/master/ensembl_prodinf/handover_client.py>`_.
