from ensembl_prodinf.email_celery_app import app
from .utils import send_email
import json
from urllib.request import urlopen

smtp_server = app.conf['smtp_server']
from_email_address = app.conf['from_email_address']
retry_wait = app.conf['retry_wait']

@app.task(bind=True)
def email_when_complete(self, url, address):
    """ Task to check a URL and send an email once the result has a non-incomplete status 
    Used for periodically checking whether a hive job has finished. If status is not complete,
    the task is retried
    Arguments:
      url - URL to check for job completion. Must return JSON containing status, subject and body fields
      address - address to send email
    """
    # allow infinite retries 
    self.max_retries = None
    result = json.load(urlopen(url))
    if (result['status'] == 'incomplete') or (result['status'] == 'running') or (result['status'] == 'submitted'):
        # job incomplete so retry task after waiting
        raise self.retry(countdown=retry_wait)
    else:
        # job complete so send email and complete task
        send_email(smtp_server=smtp_server, from_email_address=from_email_address, to_address=address, subject=result['subject'], body=result['body'])
        return result

@app.task(bind=True)
def email(self, address, subject, body):
    """ Simple task to send an email as specified
    Arguments:
      smtp_server
      from_email_address
      subject
      body
    """
    send_email(smtp_server=smtp_server,
               from_email_address=from_email_address,
               address=address,
               subject=subject,
               body=body)

