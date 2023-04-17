import urllib3
import pytest
from ensembl.production.datacheck.app.main import app
from ensembl.production.datacheck.es import ElasticsearchConnectionManager
from elasticsearch import Elasticsearch
import json
import os

dc_success_result_es_doc =   {
		"job_id": "1",
		"input_details": {
			"datacheck_groups": [],
			"server_uri": None,
			"config_file": None,
			"datacheck_names": [
				"SpeciesCommonName"
			],
			"dbname": [
				"mus_musculus_core_107_39"
			],
			"datacheck_types": [],
			"registry_file": "/hps/software/users/ensembl/ensw/registries/production/st1b.pm",
			"timestamp": "Fri Jul  1 15:12:42 2022",
			"db_type": "core",
			"target_url": None,
			"server_url": None,
			"tag": "Vertebrate  datachecks, pre-handover to web ()"
		},
		"division": "EnsemblVertebrates",
		"content": {},
		"file": "/homes/user/test_es_output/user_sL2nmrNTRkjE/results_by_species.json"
	}


dc_failed_result_es_doc =   {
		"job_id": "2",
		"input_details": {
			"datacheck_groups": [],
			"server_uri": None,
			"config_file": None,
			"datacheck_names": [
				"SpeciesCommonName"
			],
			"dbname": [
				"mus_musculus_core_107_39"
			],
			"datacheck_types": [],
			"registry_file": "/hps/software/users/ensembl/ensw/registries/production/st1b.pm",
			"timestamp": "Fri Jul  1 15:12:42 2022",
			"db_type": "core",
			"target_url": None,
			"server_url": None,
			"tag": "Vertebrate  datachecks, pre-handover to web ()"
		},
		"division": "EnsemblVertebrates",
		"content": {
          "camarhynchus_parvulus, core, camarhynchus_parvulus_core_108_11, EnsemblVertebrates" : {
            "CompareMetaKeys" : {
                "ok" : 0,
                "tests" : {
                    "not ok 4 - Gene IDs, positions, and biotype groups are the same between camarhynchus_parvulus_core_108_11 and camarhynchus_parvulus_core_107_11" : [
                    "  Failed test 'Gene IDs, positions, and biotype groups are the same between camarhynchus_parvulus_core_108_11 and camarhynchus_parvulus_core_107_11'",
                    "  at /hps/software/users/ensembl/repositories/enseven/ensembl-datacheck/lib/Bio/EnsEMBL/DataCheck/Checks/CompareMetaKeys.pm line 143.",
                    "    Structures begin differing at:",
                    "         $got->{ENSCPVG00005007000} = Does not exist",
                    "    $expected->{ENSCPVG00005007000} = HASH(0x568a2c0)",
                    "Looks like you failed 1 test of 4."
                    ]
                }
            }
        },
          "corvus_moneduloides, core, corvus_moneduloides_core_108_1, EnsemblVertebrates" : {
            "CompareMetaKeys" : {
                "ok" : 0,
                "tests" : {
                    "not ok 4 - Gene IDs, positions, and biotype groups are the same between corvus_moneduloides_core_108_1 and corvus_moneduloides_core_107_1" : [
                    "  Failed test 'Gene IDs, positions, and biotype groups are the same between corvus_moneduloides_core_108_1 and corvus_moneduloides_core_107_1'",
                    "  at /hps/software/users/ensembl/repositories/enseven/ensembl-datacheck/lib/Bio/EnsEMBL/DataCheck/Checks/CompareMetaKeys.pm line 143.",
                    "    Structures begin differing at:",
                    "         $got->{ENSCMUG00005009949} = Does not exist",
                    "    $expected->{ENSCMUG00005009949} = HASH(0x78dd4f0)",
                    "Looks like you failed 1 test of 4."
                    ]
                }
            }
        }
        },
		"file": "/homes/user/test_es_output/user_sL3mnrNTRrr1/results_by_species.json"
	}


def wait_for(url: str, retries: int = 2, backoff: float = 0.2):
    retry = urllib3.Retry(
        total=retries,
        backoff_factor=backoff,
        status_forcelist=[404, 500, 502, 503, 504],
    )
    manager = urllib3.PoolManager(retries=retry)
    manager.request("GET", url)

@pytest.fixture(scope="session")
def elastic_search():
    wait_for(f"http://localhost:9200/")
    with ElasticsearchConnectionManager("localhost", "9200", "", "", False) as es_client:
        es = es_client.client
        print("EsInfo", es.info())
        def search(body: dict) -> None:
            es.indices.flush()
            es.indices.refresh()
            return es.search(index="datacheck_results", body=body)

        try:
            #set mock es data
            es.index(index="datacheck_results", body=dc_success_result_es_doc, doc_type="report")
            es.index(index="datacheck_results", body=dc_failed_result_es_doc, doc_type="report")
            print("Index created")
            yield search
        except:
            raise RuntimeWarning("Unable to create indexes!")
        finally:
            if es.indices.exists("datacheck_results"):
                es.indices.delete("datacheck_results")

@pytest.fixture()
def es_query():
    return {
                "query": {
                    "term": {
                        "division.keyword": "EnsemblVertebrates"
                    },
                    "term": {
                        "file.keyword": "/homes/user/test_es_output/user_sL2nmrNTRkjE/results_by_species.json"
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
            }

    
@pytest.fixture
def appclient():
    app.config['ENS_VERSION'] = '108'
    app.config['TESTING'] = True
    app.config['ES_HOST'] ='localhost'
    app.config['ES_PORT'] = '9200'
    app.config['ES_USER'] = ''
    app.config['ES_PASSWORD'] = ''
    app.config['ES_SSL'] = False
    app.config['APP_ES_DATA_SOURCE'] = True
    app.config['ES_INDEX'] = 'datacheck_results'

    with app.test_client() as appclient:
        yield appclient

    

