************************
Automatic job processing
************************

Overview
########

There are a number of scenarios for which an automated job processing framework is needed, but for which eHive is not appropriate. This includes coordinated processing of input data and periodic checking of results for email alerting.

For this, `Celery<http://www.celeryproject.org/>` is a good match. This is a Python framework that uses workers to process items from a task queue. Currently, the task queue is `RabbitMQ<http://www.rabbitmq.com/>`

Installation
############

1. Starting rabbitmq

Ensure that rabbitmq is installed (either as part of the OS or as a standalone installation). You may need to enable the management console e.g ::
  ./sbin/rabbitmq-plugins enable rabbitmq_management
  ./sbin/rabbitmqctl add_user admin s3cr3t
  ./sbin/rabbitmqctl set_user_tags admin administrator
  ./sbin/rabbitmqctl set_permissions -p / admin ".*" ".*" ".*"

To start rabbitmq::
  ./sbin/rabbitmq
  
You can see the admin console (if you enabled it) at `<http://localhost:15672/`

2. Configuring celery

The celery integration provided externalises configuration to a Python module `celery_app_config.py`. This must be on your python path (e.g. in the current directory). An example file is provided as `celery_app_config.py.example` - please make a copy and edit as required. By default, this assumes your RabbitMQ server is on the same host using the default ports.

3. Starting celery

To start a celery worker::
  celery -A ensembl_prodinf worker -l info

This can then be used by any client configured to use the same backend.

Usage
#####

Assuming that the `ensembl_prodinf` package is on your pythonpath, and you also have a suitable `celery_app_config.py` module, you can submit celery tasks from the `ensembl_prodinf` package::
  from ensembl_prodinf.tasks import email_when_complete
  import time
  results = email_when_complete.delay("http://ens-prod-1.ebi.ac.uk:5000/results_email/1","dstaines@ebi.ac.uk")
  while results.ready() == False:
     print "Sleeping..."
     time.sleep(10)
  print results.get()

