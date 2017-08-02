from ensembl_prodinf.celery_app import app
from .utils import send_email
import getpass
import json
import urllib2



@app.task(bind=True)
def email_when_complete(self, url, address):
    """ Task to check a URL and send an email once the result has a non-incomplete status 
    Used for periodically checking whether a hive job has finished.
    """

    # allow infinite retries 
    self.max_retries = None
    result = json.load(urllib2.urlopen(url))
    if result['status'] == 'incomplete':
        raise self.retry()
    else:
        from_email = "%s@ebi.ac.uk" % getpass.getuser()
        smtp_server = 'localhost'
        send_email(smtp_server, from_email, address, result['subject'], result['body'])
        return result

