from ensembl_prodinf.handover_tasks import handover_database
import logging
import json
logging.basicConfig(level=logging.DEBUG)
spec = {
    'src_uri':"mysql://ensro@mysql-eg-enaprod.ebi.ac.uk:4346/saccharomyces_cerevisiae_core_38_91_4", 
    'tgt_uri':"mysql://ensrw:writ3rp3@mysql-eg-prod-3.ebi.ac.uk:4243/saccharomyces_cerevisiae_core_38_91_4", 
    'contact':"dstaines@ebi.ac.uk", 'type':"update", 'comment':"new stuff, innit"}
x = handover_database(spec)
logging.info(x)
