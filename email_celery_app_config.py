import os
import getpass
broker_url = os.environ.get("CELERY_BROKER_URL", 'pyamqp://')
result_backend = os.environ.get("CELERY_RESULT_BACKEND", 'rpc://')
smtp_server = os.environ.get("SMTP_SERVER", 'localhost')
from_email_address = os.environ.get("FROM_EMAIL_ADDRESS", "%s@ebi.ac.uk" % getpass.getuser())
retry_wait = int(os.environ.get("RETRY_WAIT", 60))
task_routes = {'ensembl_prodinf.email_tasks': {'queue': 'email'}}