from contextlib import contextmanager
from elasticsearch import Elasticsearch, TransportError, NotFoundError, ElasticsearchException
from ensembl.production.datacheck.config import DatacheckConfig as dcg


class ElasticsearchConnectionManager():
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.client = None

    def __enter__(self):
        self.client = Elasticsearch([{'host': self.host, 'port': self.port}])
        if not self.client.ping():
            raise(
                f"Cannot connect to Elasticsearch server. Host: {dcg.es_host}, Port: {dcg.es_port}"
             )
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.client.transport.close()



def get_datacheck_results(division:str, jsonfile_path:str, 
                          es_host: str = dcg.ES_HOST, 
                          es_port: str = dcg.ES_PORT,
                          es_index: str = dcg.ES_INDEX
                          ) :
    """Get datacheck results stored in Elasticsearch

    Args:
        division (str): Ensembl division to filter results
        jsonfilename (str): unique file name to filter the results
        es_host (str): elastic search host to connect 
        es_port (str): elastic search port 
        es_index (str): elastic search index where dc results are stored

    Returns:
        dict: status with elasticsearch response 
    """  

    if not all([division, jsonfile_path]):
       raise Exception("Param division and jsonfile_path required")
     
    with ElasticsearchConnectionManager(es_host, es_port) as es:
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