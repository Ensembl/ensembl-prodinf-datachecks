Overview
========
The Celery task manager is currently used for scheduling checks on completed jobs and sending emails.

Tasks for this are defined in `ensembl-prodinf-core <https://github.com/Ensembl/ensembl-prodinf-core>`_ - for more information please see `celery.rst <https://github.com/Ensembl/ensembl-prodinf-core/blob/master/docs/celery.rst>`_

Installation
============

Requirements for the Celery email worker service are in `celery_requirements.txt <../celery_requirements.txt>`_ which can be installed using ``pip```:

.. code-block:: bash

  pip install -f celery_requirements.txt

This will install ``ensembl_prodinf`` from git - alternatively to reference an existing install to PYTHONPATH e.g.

.. code-block:: bash

  PYTHONPATH=dir/ensembl-prodinf/ensembl-prodinf-core

The default backend is RabbitMQ. This can be installed as per https://www.rabbitmq.com/.

Once installed, configuration is read from the module ``celery_email_config`` from ``PYTHONPATH``. This can be modified directly, or the following environment variables can be supplied at run time:

* ``CELERY_BROKER_URL`` - celery queue broker (default is ``pyamqp://``)
* ``CELERY_RESULT_BACKEND`` - backend for celery to store results (default is ``rpc://``)
* ``SMTP_SERVER`` - server for sending email (default is ``localhost``)
* ``FROM_EMAIL_ADDRESS`` - address to send emails from (default is current user @ebi)
* ``RETRY_WAIT`` - seconds to wait between polling for task success (default is 60 seconds)


Running Celery
==============

To start a celery worker to handle email:

.. code-block:: bash

  celery -A ensembl_prodinf.email_tasks worker -l info -Q email -n email@%h

Using Docker
============

To build a Docker image:

.. code-block:: bash

  docker build -t ensembl_prodinf/celery_email_app -f Dockerfile.celery_email .


To run your Docker image against a specified rabbitMQ instance, exposing the REST service on port 4001 e.g.:

.. code-block:: bash

  docker run -p 127.0.0.1:4001:4001 --env HIVE_URI='mysql://user:pwd@localhost:3306/my_hive_db' ensembl_prodinf/hc_app


Environment variables should be supplied as arguments to the run command as shown in the example above.
