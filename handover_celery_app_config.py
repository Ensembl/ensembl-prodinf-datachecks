import os
import getpass
from ensembl_prodinf.config import load_yaml


config_file_path = os.environ.get('HANDOVER_CELERY_CONFIG_PATH')
if config_file_path:
    file_config = load_yaml(config_file_path)
else:
    file_config = {}

broker_url = os.environ.get("CELERY_BROKER_URL",
                            file_config.get('celery_broker_url', 'pyamqp://'))
result_backend = os.environ.get("CELERY_RESULT_BACKEND",
                                file_config.get('celery_result_backend', 'rpc://'))
smtp_server = os.environ.get("SMTP_SERVER",
                             file_config.get('smtp_server', 'localhost'))
from_email_address = os.environ.get("FROM_EMAIL_ADDRESS",
                                    file_config.get('from_email_address', "%s@ebi.ac.uk" % getpass.getuser()))
retry_wait = int(os.environ.get("RETRY_WAIT",
                                file_config.get('retry_wait', 60)))

task_routes = {'ensembl_prodinf.handover_tasks.*': {'queue': 'handover'}}
