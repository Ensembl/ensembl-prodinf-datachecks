'''
Created on 13 Dec 2017

@author: dstaines
'''
import datetime
import socket

import requests


class Reporter:
    
    def __init__(self, uri, process):
        self.uri = uri
        self.process = process
    
    def report(self, resource, report_type, message, **kwargs):
        process = kwargs.get('host', self.process)
        host = kwargs.get('host', socket.gethostname())
        time = kwargs.get('timestamp', datetime.datetime.now())
        r = requests.post(self.uri, json={
            'resource':resource,
            'process':process,
            'report_type':report_type,
            'message':message,
            'host':host,
            'report_time':time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            })
        r.raise_for_status()
        return r.json()['token']
