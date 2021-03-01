************************
Automatic job processing
************************

Overview
########

There are a number of scenarios for which an automated job processing framework is needed, but for which eHive is not appropriate. This includes coordinated processing of input data and periodic checking of results for email alerting.

For this, Celery_ is a good fit. This is a Python framework that uses workers to process items from a task queue. Currently, the task queue is RabbitMQ_.

Installation
############

1. Starting rabbitmq
====================

Ensure that rabbitmq is installed (either as part of the OS or as a standalone installation). You may need to enable the management console e.g

.. code-block:: bash

  ./sbin/rabbitmq-plugins enable rabbitmq_management
  ./sbin/rabbitmqctl add_user admin s3cr3t
  ./sbin/rabbitmqctl set_user_tags admin administrator
  ./sbin/rabbitmqctl set_permissions -p / admin ".*" ".*" ".*"

To start rabbitmq:

.. code-block:: bash

  ./sbin/rabbitmq
  
You can see the admin console (if you enabled it) at http://localhost:15672/

2. Configuring celery
=====================

The celery integrations provided externalise configuration to Python modules such as `email_celery_app_config.py`_ and `handover_celery_app_config.py`_. This must be on your python path (e.g. in the current directory) for any applications that use these tasks e.g. `flask` for submitting tasks, and `celery` workers for processing them.

These config files can provide configuration in whatever way is most suitable, but the standard approach is to allow configuration values to be taken from either an environment variable or a supplied default. This approach fits well with running these services using Docker.

Configuration falls into two main categories - celery-specific configuration such as the location of the RabbitMQ backend, and task-specific configuration. Note that different tasks can be directed to different queues to allow workers to be separated by task type.

3. Starting celery
==================

To start a celery worker to process `email_tasks`:

.. code-block:: bash

  celery -A ensembl_prodinf.email_tasks worker -l info

This will then process tasks from this package that are submitted by other clients e.g. `flask`.

Usage
#####

There are currently three sets of celery tasks in `ensembl_prodinf`:

- email_tasks_ - generic tasks to poll a supplied URL and send email once the URL returns results. This is used to alert users of the self-service healthcheck and copy services that their jobs have completed.
- handover_tasks_ - tasks for coordinated processing of data handed over to staging. These tasks follow a common pattern of invoking a service, then creating new tasks as required once the service has completed. See `Handover Service`_ for more details.
- event_tasks_ - tasks for scheduling new processing in response to metadata events. See `Event Service`_ for more details.

Assuming that the `ensembl_prodinf` package is on your pythonpath, and you also have a suitable `email_celery_app_config.py` module, you can submit celery tasks from the `ensembl_prodinf` package:

.. code-block:: python

  from ensembl_prodinf.email_tasks import email_when_complete
  import time
  results = email_when_complete.delay("http://ens-prod-1.ebi.ac.uk:5000/jobs/1?format=email","dstaines@ebi.ac.uk")
  while results.ready() == False:
     print "Sleeping..."
     time.sleep(10)
  print results.get()


.. _Celery: http://www.celeryproject.org/
.. _RabbitMQ: http://www.rabbitmq.com/
.. _email_tasks: ../ensembl_prodinf/email_tasks.py
.. _handover_tasks: ../ensembl_prodinf/handover_tasks.py
.. _event_tasks: ../ensembl_prodinf/event_tasks.py
.. _`Handover Service`: ./handover.rst
.. _`Event Service`: ../event_processing.rst
.. _`email_celery_app_config.py` : ../email_celery_app_config.py
.. _`handover_celery_app_config.py` : ../handover_celery_app_config.py