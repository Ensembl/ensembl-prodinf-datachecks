from celery import Celery
import handover_celery_app_config

app = Celery('ensembl_prodinf',
             include=['ensembl_prodinf.handover_tasks'])

# Load the externalised config module from PYTHONPATH
app.config_from_object('handover_celery_app_config')

if __name__ == '__main__':
    app.start()
