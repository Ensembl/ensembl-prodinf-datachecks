# .. See the NOTICE file distributed with this work for additional information
#     regarding copyright ownership.
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#         http://www.apache.org/licenses/LICENSE-2.0
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
import json


def test_without_jsonfile_param(appclient):
    response = appclient.get('/jobs/details')
    data = json.loads(response.data)
    assert response.status_code == 404
    assert data['error'] == 'Failed to retrieve the details : jsonfile needed '


def test_get_dc_results_success(appclient, elastic_search, es_query):
    elastic_search(es_query)
    response = appclient.get(
        '/jobs/details?jsonfile=/homes/user/test_es_output/user_sL2nmrNTRkjE/results_by_species.json')
    data = json.loads(response.data)
    assert response.status_code == 200
    assert data == {}


def test_get_dc_results_failed(appclient, elastic_search, es_query):
    elastic_search(es_query)
    response = appclient.get(
        '/jobs/details?jsonfile=/homes/user/test_es_output/user_sL3mnrNTRrr1/results_by_species.json')
    data = json.loads(response.data)
    assert response.status_code == 200
    assert len(data.keys()) == 2
