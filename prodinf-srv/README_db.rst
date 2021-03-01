Overview
========

The database copy service provides a set of endpoints to allow MySQL databases to be copied between servers. These endpoints can be used "self-service" by members of the team, or programatically by components of the Ensembl Production infrastructure.

Implementation
==============

The endpoints are defined in `db_app.py <db_app.py>`_ flask app. They use the
`ensembl-prodinf-core <https://github.com/Ensembl/ensembl-prodinf-core>`_ libraries for scheduling and monitoring Hive
jobs. The endpoints use the `HiveInstance <https://github.com/Ensembl/ensembl-prodinf-core/blob/master/ensembl_prodinf/hive.py>`_
class to submit copy jobs to a hive database generated from
`Bio::EnsEMBL::Production::Pipeline::PipeConfig::CopyDatabase_conf <https://github.com/Ensembl/ensembl-production/blob/master/modules/Bio/EnsEMBL/Production/Pipeline/PipeConfig/CopyDatabase_conf.pm>`_
which should then be handled by a running beekeeper instance. For more information on how hive is used by this service,
please see `hive.rst <https://github.com/Ensembl/ensembl-prodinf-core/blob/master/docs/hive.rst>`_.

After the flask app has been started consult ``/apidocs`` for complete endpoint documentation.

Optionally, when jobs are submitted an email address can be supplied for an email to be sent to when the job completes or fails. This is as described in `README_celery_email.rst <./README_celery_email.rst>`_.

Installation
============

First clone this repo

.. code-block:: bash

  git clone https://github.com/Ensembl/ensembl-prodinf-srv
  cd ensembl-prodinf-srv

To install Python requirements using pip:

.. code-block:: bash

  pip install -r requirements.txt

This will install ``ensembl_prodinf`` from git - alternatively to reference an existing install to PYTHONPATH e.g.

.. code-block:: bash

  PYTHONPATH=[install_dir]/ensembl-prodinf/ensembl-prodinf-core

Hive Setup
==========
Before you can use the HC endpoint, you need a beekeeper running the pipeline defined by ``Bio::EnsEMBL::Production::Pipeline::PipeConfig::CopyDatabase_conf``. To build and initiate the pipeline:

.. code-block:: bash

  git clone https://github.com/Ensembl/ensembl-production
  cd ensembl-production
  SRV=your_mysql_command_wrapper from where your hive will be running.
  init_pipeline.pl Bio::EnsEMBL::Production::Pipeline::PipeConfig::CopyDatabase_conf $($SRV details hive)

Next, run the ``beekeeper.pl`` supplied by the output with the arguments ``--keep_alive -sleep 0.5``. This ensures the hive runs continually, picking up new jobs as they are submitted.
The current hive version compatible with this service is 2.5

Configuration
=============
There are two configuration files you need to have copies of locally.

.. code-block:: bash

  cp celery_app_config.py.example celery_app_config.py

Secondly, you can provide an instance file, the location of which depends if you're using virtualenv or not.

For virtualenv:

.. code-block:: bash

  mkdir -p instance
  cp db_config.py.instance_example instance/db_config.py
  cp server_uris.json.example server_uris.json

Otherwise:

.. code-block:: bash

  mkdir instance
  cp db_config.py.instance_example instance/db_config.py

Edit them as required. SERVER_URIS_FILE must point to a JSON file containing lists of server names for autocomplete e.g.

.. code-block:: bash

  SERVER_URIS_FILE = 'server_uris.json'
  HIVE_URI='mysql://myuser:mypass@myhost:3306/standalone_db_hive'

An example can be found in ``server_uris.json.example``.

Note that you can leave instance files empty, and use the defaults found in db_config.py, or override them at run time with environment variables.

The following environment variables are supported:

* ``SERVER_URIS_FILE`` - path to JSON file containing server details
* ``HIVE_URI`` - mysql URI of DB copy hive database
* ``HIVE_ANALYSIS`` - name of analysis for submitting new jobs to the hive (not usually needed to be changed)
* ``CELERY_BROKER_URL`` - URL of Celery broker
* ``CELERY_RESULT_BACKEND`` - URL of Celery backend

Running Celery
==============
See `README_celery_email.rst <./README_celery_email.rst>`_ about how to run a Celery worker to monitor jobs.

Running
=======
Important: for the status endpoint to work, you must run the app as a user who can ssh onto any servers you want to find the status for.

To start the main application as a standalone Flask application:

.. code-block:: bash

  export FLASK_APP=db_app.py
  cd ensembl-prodinf-srv
  flask run --port 5002 --host 0.0.0.0

or to start the main application as a standalone using gunicorn with 4 threads:

.. code-block:: bash

  pyenv activate ensprod_inf
  cd ensembl-prodinf-srv
  gunicorn -w 4 -b 0.0.0.0:5002 db_app:app

Note that for production, a different deployment option should be used as the standalone flask app can only serve one request at a time.


Client
======

A simple Python REST client for this app can be found in `db_copy_client.py <https://github.com/Ensembl/ensembl-prodinf-core/blob/master/ensembl_prodinf/db_copy_client.py>`_.


Using Docker
============

To build a Docker image, first copy ``ssh_config.example`` to ``ssh_config`` and make any changes required (e.g. path to ssh keys) and then build:

.. code-block:: bash

  docker build -t ensembl_prodinf/db_app -f Dockerfile.db .

Supported environment variables (see above) should be supplied as arguments to the run command as shown in the example above.

The database status endpoint relies on certificate-based SSH to other machines, so the container needs access to the identity files specified in the ssh_config file. For the example file provided, you must mount a directory containing ``id_rsa`` and ``id_rsa.pub`` using the path specified in the `ssh_config` file using the `--mount` argument.

In addition, the file specified in ``SERVER_URIS`` must also be available. Again, this can be provided with an additional volume using the ``--mount`` argument.

To run your Docker image against a specified hive, exposing the REST service on port 4002 e.g.:

.. code-block:: bash

  docker run -p 127.0.0.1:4002:4002 \
       --mount type=bind,src=$PWD/ssh_keys/,target=/ssh_keys/ \
       --mount type=bind,src=$PWD/server_uris/,target=/server_uris \
       --env HIVE_URI='mysql://user:pwd@localhost:3306/my_hive_db' \
       --env SERVER_URIS_FILE='/server_uris/server_uris.json' \
       ensembl_prodinf/db_app
