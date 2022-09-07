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

import logging
import os
import pathlib
import pkg_resources
import urllib3
import urllib
import json 
import requests.exceptions
from pathlib import Path

from ensembl.production.core.config import load_config_yaml

from ensembl.utils.rloader import RemoteFileLoader

pathlib.Path(__file__).parent.absolute()

config_file_path = os.environ.get('DATACHECK_CONFIG_PATH', os.path.dirname(__file__) + '/datachecks_config.dev.yaml')
from flask.logging import default_handler

logger = logging.getLogger()
logger.addHandler(default_handler)


def get_app_version():
    try:
        version = pkg_resources.require("datacheck")[0].version
    except Exception as e:
        with open(Path(__file__).parents[4] / 'VERSION') as f:
            version = f.read()
    return version

def get_server_names(url, flag=0):
    if flag :
        url=urllib.parse.urljoin(url, '/api/dbcopy/dcserversnames')
        logger.warning(f"Fetching Allowed dc server host names from {url}")
        retry = urllib3.Retry(
            total=10,
            backoff_factor=0.2,
            status_forcelist=[404, 500, 502, 503, 504],
        )
        http = urllib3.PoolManager(retries=retry)
        response = http.request("GET", url)
        if response.status != 200:
            raise ValueError(f"Check DBcopy service is ready {url}")

        logger.warning(f"loaded dc server host names from {url}")
        return json.loads(response.data.decode('utf-8'))
    else:
        server_file_path = os.environ.get("SERVER_NAMES", EnsemblConfig.file_config.get('server_names_file',
                                                                                     os.path.join(
                                                                                         os.path.dirname(__file__),
                                                                                         'server_names.dev.json')))
        return json.load(open(server_file_path))

class DCConfigLoader:
    base_uri = 'https://raw.githubusercontent.com/Ensembl/ensembl-datacheck/'
    uri = base_uri + 'release/{}/lib/Bio/EnsEMBL/DataCheck/index.json'

    @classmethod
    def load_config(cls, version=None):
        loader = RemoteFileLoader('json')
        uri = cls.uri.format(version)
        try:
            return loader.r_open(uri)
        except requests.exceptions.HTTPError as e:
            logger.warning(f"Load versioned index.json error: {version}")
            logger.warning("No version specified, fallback on `main` branch")
            uri = cls.base_uri + 'main/lib/Bio/EnsEMBL/DataCheck/index.json'
            # should always be available uri.
            return loader.r_open(uri)


class EnsemblConfig:
    file_config = load_config_yaml(config_file_path)

    ENS_VERSION = os.environ.get("ENS_VERSION")
    SCRIPT_NAME = os.environ.get('SCRIPT_NAME', '')
    BASE_DIR = os.environ.get('BASE_DIR',
                              file_config.get('base_dir'))
    SECRET_KEY = os.environ.get('SECRET_KEY',
                                file_config.get('secret_key', os.urandom(32)))
    SERVER_URIS_FILE = os.environ.get('SERVER_URIS_FILE',
                                      file_config.get('server_uris_file', 'server_uris_list.json'))
    SWAGGER = {
        'title': 'Ensembl Datacheck Service',
        'uiversion': 3,
        'hide_top_bar': True,
        'ui_params': {
            'defaultModelsExpandDepth': -1
        },
        'favicon': '/img/production.png'
    }


class DatacheckConfig(EnsemblConfig):
    DATACHECK_INDEX = DCConfigLoader.load_config(EnsemblConfig.ENS_VERSION)

    DATACHECK_COMMON_DIR = os.environ.get("DATACHECK_COMMON_DIR",
                                          EnsemblConfig.file_config.get('datacheck_common_dir', '~/datachecks'))
    DATACHECK_CONFIG_DIR = os.path.join(DATACHECK_COMMON_DIR, 'config')
    DATACHECK_REGISTRY_DIR = os.path.join(DATACHECK_COMMON_DIR, 'registry')
    HIVE_ANALYSIS = os.environ.get("HIVE_ANALYSIS",
                                   EnsemblConfig.file_config.get('hive_analysis', 'DataCheckSubmission'))
    HIVE_URI = os.environ.get("HIVE_URI", EnsemblConfig.file_config.get('hive_uri'))
    SERVER_NAMES_FILE = os.environ.get("SERVER_NAMES", EnsemblConfig.file_config.get('server_names_file',
                                                                                     os.path.join(
                                                                                         os.path.dirname(__file__),
                                                                                         'server_names.dev.json')))
    SWAGGER_FILE = os.environ.get("SWAGGER_FILE",
                                  EnsemblConfig.file_config.get('swagger_file',
                                                                f"{pathlib.Path().absolute()}/swagger.yml"))
    COPY_URI_DROPDOWN = os.environ.get("COPY_URI_DROPDOWN",
                                       EnsemblConfig.file_config.get('copy_uri_dropdown',
                                                                     "http://localhost:80/"))

    DATACHECK_TYPE = os.environ.get('DATACHECK_TYPE', EnsemblConfig.file_config.get('datacheck_type', 'vertebrates'))
    
    APP_ES_DATA_SOURCE = os.environ.get('APP_ES_DATA_SOURCE', EnsemblConfig.file_config.get('app_es_data_source', True))
    
    ES_HOST = os.environ.get('ES_HOST', EnsemblConfig.file_config.get('es_host', 'localhost'))
    
    ES_PORT = os.environ.get('ES_PORT', EnsemblConfig.file_config.get('es_port', '9200'))
    
    ES_INDEX = os.environ.get('ES_INDEX', EnsemblConfig.file_config.get('es_index', f"datacheck_results_{EnsemblConfig.ENS_VERSION}"))
    
    GET_SERVER_NAMES = os.environ.get('GET_SERVER_NAMES', EnsemblConfig.file_config.get('get_server_ names', 0))

    SERVER_NAMES = get_server_names(COPY_URI_DROPDOWN, GET_SERVER_NAMES)

    APP_VERSION =  get_app_version()
