from celery import Celery
import email_celery_app_config

app = Celery('ensembl_prodinf',
             include=['ensembl_prodinf.email_tasks'])

# Load the externalised config module from PYTHONPATH
app.config_from_object('email_celery_app_config')


if __name__ == '__main__':
    app.start()
