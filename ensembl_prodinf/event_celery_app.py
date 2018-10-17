import logging

from celery import Celery, exceptions as cel_exceptions

app = Celery('ensembl_prodinf',
             include=['ensembl_prodinf.event_tasks'])

# Load the externalised config module from PYTHONPATH
try:
    import event_celery_app_config

    app.config_from_object('event_celery_app_config')
except cel_exceptions.CeleryError:
    logging.warning('Celery email requires event_celery_app_config module')
if __name__ == '__main__':
    app.start()
