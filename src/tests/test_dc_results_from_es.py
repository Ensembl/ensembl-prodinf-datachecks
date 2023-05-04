import urllib3
import pytest
import json


            
def test_without_jsonfile_param(appclient):
    response = appclient.get('/jobs/details')
    data = json.loads(response.data)
    assert response.status_code == 404
    assert data['error'] == 'Failed to retrieve the details : jsonfile needed '

def test_get_dc_results_success(appclient, elastic_search, es_query):
    elastic_search(es_query)
    response = appclient.get('/jobs/details?jsonfile=/homes/user/test_es_output/user_sL2nmrNTRkjE/results_by_species.json')
    data = json.loads(response.data)
    assert response.status_code == 200
    assert data == {}

def test_get_dc_results_failed(appclient, elastic_search, es_query):
    elastic_search(es_query)
    response = appclient.get('/jobs/details?jsonfile=/homes/user/test_es_output/user_sL3mnrNTRrr1/results_by_species.json')
    data = json.loads(response.data)
    assert response.status_code == 200
    assert len(data.keys()) == 2

