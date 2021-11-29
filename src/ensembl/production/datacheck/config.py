# .. See the NOTICE file distributed with this work for additional information
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

import os
import warnings

import requests.exceptions
import sys
from ensembl.production.core.config import load_config_yaml
import pathlib
from ensembl.utils.rloader import RemoteFileLoader

pathlib.Path(__file__).parent.absolute()

config_file_path = os.environ.get('DATACHECK_CONFIG_PATH')
file_config = load_config_yaml(config_file_path)


class DCConfigLoader:
    base_uri = 'https://raw.githubusercontent.com/Ensembl/ensembl-datacheck/'
    uri = base_uri + 'release/{}/lib/Bio/EnsEMBL/DataCheck/index.json'

    @classmethod
    def load_config(cls, version=''):
        loader = RemoteFileLoader('json')
        uri = cls.uri.format(version)
        try:
            return loader.r_open(uri)
        except requests.exceptions.HTTPError:
            warnings.warn(f"Unable to load versioned index.json from {uri}")
            try:
                uri = cls.base_uri + 'main/lib/Bio/EnsEMBL/DataCheck/index.json'
                return loader.r_open(uri)
            except requests.exceptions.HTTPError:
                warnings.warn(f"Unable to load main from {uri}")
        return {}


class EnsemblConfig:
    ENS_VERSION = os.environ.get("ENS_VERSION", '500')
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
                                          file_config.get('datacheck_common_dir', '~/datachecks'))
    DATACHECK_CONFIG_DIR = os.path.join(DATACHECK_COMMON_DIR, 'config')
    DATACHECK_REGISTRY_DIR = os.path.join(DATACHECK_COMMON_DIR, 'registry')
    HIVE_ANALYSIS = os.environ.get("HIVE_ANALYSIS",
                                   file_config.get('hive_analysis', 'DataCheckSubmission'))
    HIVE_URI = os.environ.get("HIVE_URI", file_config.get('hive_uri'))
    SERVER_NAMES_FILE = os.environ.get("SERVER_NAMES", file_config.get('server_names_file',
                                                                       os.path.join(os.path.dirname(__file__),
                                                                                    'server_names.dev.json')))
    SWAGGER_FILE = os.environ.get("SWAGGER_FILE",
                                  file_config.get('swagger_file', f"{pathlib.Path().absolute()}/swagger.yml"))
    COPY_URI_DROPDOWN = os.environ.get("COPY_URI_DROPDOWN",
                                       file_config.get('copy_uri_dropdown',
                                                       "http://production-services.ensembl.org:80/"))

    DATACHECK_TYPE = os.environ.get('DATACHECK_TYPE', file_config.get('datacheck_type', 'metazoa'))
