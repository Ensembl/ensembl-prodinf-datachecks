from celery import Celery
import celery_app_config

app = Celery('ensembl_prodinf',
             include=['ensembl_prodinf.tasks'])

app.config_from_object('celery_app_config')


if __name__ == '__main__':
    app.start()
