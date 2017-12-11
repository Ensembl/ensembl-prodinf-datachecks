'''
Created on 4 Dec 2017

@author: dstaines
'''
from datetime import datetime
from ensembl_prodinf.handover_celery_app import app
import logging
from json import JSONEncoder

class HandoverSpec(JSONEncoder):
    def __init__(self, src_uri, tgt_uri, username, update_type, comment, timestamp=datetime.now().isoformat()):
        self.src_uri = src_uri
        self.tgt_uri = tgt_uri
        self.username = username
        self.update_type = update_type
        self.comment = comment
        self.timestamp = timestamp

    def default(self, obj):
        print "Encoding"
        return JSONEncoder.default(self, self.__dict__)
        
def handover_database(spec):
    logging.info("Thanks for "+str(spec))
    check_db(spec['src_uri'])
    check_registry(spec)
    hc_token = submit_hc(spec['src_uri'])    
    token = process_checked_db.delay(spec, hc_token)
    return token
    
def check_db(uri):    
    logging.info(uri+" looks good to me")
    return

def check_registry(spec):
    logging.info(spec['src_uri']+" looks good to el reg")
    return
    
def submit_hc(uri):
    return 'banana'

@app.task(bind=True)    
def process_checked_db(self, spec, hc_token):
    logging.info("Checking "+str(spec)+" using "+hc_token)
    copy_token = submit_copy(spec['src_uri'], spec['tgt_uri'])    
    token = process_copied_db.delay(spec, copy_token)
    return token

def submit_copy(src_uri, tgt_uri):
    return 'mango'

@app.task(bind=True)    
def process_copied_db(self, spec, copy_token):
    logging.info("Checking "+str(spec)+" using "+copy_token)
        
    return spec

def add_to_metadata(spec):
    return