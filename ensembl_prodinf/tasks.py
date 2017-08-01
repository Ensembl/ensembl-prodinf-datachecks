from ensembl_prodinf.celery_app import app
from email.mime.text import MIMEText
from smtplib import SMTP
import getpass
import json
import urllib2

from_email = "%s@ebi.ac.uk" % getpass.getuser()

def send_email(address, subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = address    
    s = SMTP('localhost')
    s.sendmail(from_email, [address], msg.as_string())
    s.quit()

@app.task(bind=True)
def email_when_complete(self, url, address):
    self.max_retries = None
    print url
    result = json.load(urllib2.urlopen(url))
    print result
    if result['status'] == 'incomplete':
        raise self.retry()
    else:
        send_email(address, result['subject'], result['body'])
        return result

