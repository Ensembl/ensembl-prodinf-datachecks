# See the NOTICE file distributed with this work for additional information
#    regarding copyright ownership.
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#        http://www.apache.org/licenses/LICENSE-2.0
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

from elasticsearch import ElasticsearchException
from sqlalchemy.engine import make_url

from ensembl.production.core.es import ElasticsearchConnectionManager
from ensembl.production.datacheck.config import DatacheckConfig as dcg


def qualified_name(db_uri):
    import re
    db_url = make_url(db_uri)
    if re.search('[a-z-]?(.ebi.ac.uk|.org)', db_url.host) or db_url.host in ('localhost', 'mysql'):
        return db_uri
    else:
        host = f'{db_url.host}.ebi.ac.uk'
        if db_url.password:
            return f"{db_url.drivername}://{db_url.username}:{db_url.password}@{host}:{db_url.port}/{db_url.database}"
        else:
            return f"{db_url.drivername}://{db_url.username}@{host}:{db_url.port}/{db_url.database}"


def get_datacheck_results(jsonfile_path: str,
                          es_host: str = dcg.ES_HOST,
                          es_port: int = int(dcg.ES_PORT),
                          es_index: str = dcg.ES_INDEX,
                          es_user: str = dcg.ES_USER,
                          es_password=dcg.ES_PASSWORD,
                          es_ssl=dcg.ES_SSL):
    """Get datacheck results stored in Elasticsearch

    Args:
        jsonfile_path (str): unique file name to filter the results
        es_host (str): elastic search host to connect 
        es_port (int): elastic search port
        es_index (str): elastic search index where dc results are stored
        es_ssl (bool): elastic connexion config
        es_password (str): elastic connexion config
        es_user (str): elastic connexion config

    Returns:
        dict: status with elasticsearch response 
    """
    with ElasticsearchConnectionManager(es_host, es_port, es_user, es_password, es_ssl) as es:
        try:
            res = es.client.search(index=es_index, body={
                "query": {
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
                raise ElasticsearchException(f"""No Hits Found for given params jsonfile_path {jsonfile_path} """)

            return {"status": True, "message": "", "result": res['hits']['hits'][0]['_source']['content']}

        except Exception as err:
            return {"status": False, "message": str(err)}
