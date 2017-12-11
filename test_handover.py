from ensembl_prodinf.handover_tasks import handover_database
import logging
import json
logging.basicConfig(level=logging.DEBUG)
spec = {'src_uri':"mydb",'tgt_uri':"yourdb",'contact':"me",'type':"update",'comment':"new stuff, innit"}
x = handover_database(spec)
logging.info(x)