'''
@author: dstaines
'''
import os
process_lookup  =  os.environ.get("PROCESS_LOOKUP", "./process_lookup.json")
report_server = os.environ.get("REPORT_SERVER", "amqp://guest:guest@localhost:5672/%2F")
report_exchange = os.environ.get("REPORT_EXCHANGE", 'report_exchange')
event_uri = os.environ.get("EVENT_URI", 'http://127.0.0.1:5004/')