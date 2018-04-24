from ensembl_prodinf.email_celery_app import app
from .utils import send_email
import json
import urllib2

smtp_server = app.conf['smtp_server']
from_email_address = app.conf['from_email_address']
retry_wait = app.conf['retry_wait']

@app.task(bind=True)
def email_when_complete(self, url, address):
    """ Task to check a URL and send an email once the result has a non-incomplete status 
    Used for periodically checking whether a hive job has finished.
    """
    # allow infinite retries 
    self.max_retries = None
    result = json.load(urllib2.urlopen(url))
    if (result['status'] == 'incomplete') or (result['status'] == 'running') or (result['status'] == 'submitted'):
        raise self.retry(countdown=retry_wait)
    else:
        send_email()
        return result

@app.task(bind=True)
def email(self, address, subject, body):
    send_email(smtp_server, from_email_address, address, subject, body)
    return

