import ssl

import urllib3
from elasticsearch import Elasticsearch, ElasticsearchException
from elasticsearch.connection import create_ssl_context

from ensembl.production.datacheck.config import DatacheckConfig as dcg


class ElasticsearchConnectionManager:
    def __init__(self, host: str , port: str, user: str, password: str, with_ssl: bool):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.ssl = with_ssl
        self.client = None

    def __enter__(self):
        urllib3.disable_warnings(category=urllib3.connectionpool.InsecureRequestWarning)
        ssl_context = create_ssl_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        self.client = Elasticsearch(hosts=[{'host': self.host, 'port': self.port}],
                           scheme="https" if self.ssl else "http",
                           ssl_context=ssl_context,
                           http_auth=(self.user, self.password))
        if not self.client.ping():
            raise(
                f"Cannot connect to Elasticsearch server. User: {dcg.ES_USER}, Host: {dcg.ES_HOST}, Port: {dcg.ES_PORT}"
             )
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.client.transport.close()



def get_datacheck_results(division:str,
                          jsonfile_path:str,
                          es_host: str = dcg.ES_HOST, 
                          es_port: str = dcg.ES_PORT,
                          es_index: str = dcg.ES_INDEX,
                          es_user: str = dcg.ES_USER,
                          es_password = dcg.ES_PASSWORD,
                          es_ssl = dcg.ES_SSL) :
    """Get datacheck results stored in Elasticsearch

    Args:
        division (str): Ensembl division to filter results
        jsonfile_path (str): unique file name to filter the results
        es_host (str): elastic search host to connect 
        es_port (str): elastic search port 
        es_index (str): elastic search index where dc results are stored
        es_ssl (bool): elastic connexion config
        es_password (str): elastic connexion config
        es_user (str): elastic connexion config

    Returns:
        dict: status with elasticsearch response 
    """

    if not all([division, jsonfile_path]):
       raise Exception("Param division and jsonfile_path required")
     
    with ElasticsearchConnectionManager(es_host, es_port, es_user, es_password, es_ssl) as es:
        es_client = es.client
        try:
            res = es_client.search(index = es_index, body={
                    "query": {
                        "term": {
                            "division.keyword": division
                        },
                        "term": {
                            "file.keyword": jsonfile_path
                        }
                    },
                    "size": 1,
                    "sort": [
                        {
                            "report_time": {
                                "unmapped_type": "keyword",
                                "order": "desc"
                            }
                        }
                    ]
            })
            if len(res['hits']['hits']) == 0:
                raise ElasticsearchException(f""" No Hits Found for given params division {division} 
                                             and jsonfile_path {jsonfile_path} """)

            return {"status": True, "message": "", "result": res['hits']['hits'][0]['_source']['content'] }
        
        except Exception as err:
            return {"status": False, "message": str(err) }