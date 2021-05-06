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
from ensembl.production.core.config import load_config_yaml
import pathlib
pathlib.Path(__file__).parent.absolute()

config_file_path = os.environ.get('DATACHECK_CONFIG_PATH')
file_config = load_config_yaml(config_file_path)


class EnsemblConfig:

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
  
    DATACHECK_INDEX = os.path.join(EnsemblConfig.BASE_DIR, 'ensembl-datacheck/lib/Bio/EnsEMBL/DataCheck/index.json')
    DATACHECK_COMMON_DIR = os.environ.get("DATACHECK_COMMON_DIR",
                                          file_config.get('datacheck_common_dir'))
    DATACHECK_CONFIG_DIR = os.path.join(DATACHECK_COMMON_DIR, 'config')
    DATACHECK_REGISTRY_DIR = os.path.join(DATACHECK_COMMON_DIR, 'registry')
    HIVE_ANALYSIS = os.environ.get("HIVE_ANALYSIS",
                                   file_config.get('hive_analysis', 'DataCheckSubmission'))
    HIVE_URI = os.environ.get("HIVE_URI", file_config.get('hive_uri'))
    SERVER_NAMES_FILE = os.environ.get("SERVER_NAMES", file_config.get('server_names_file'))
    SWAGGER_FILE = os.environ.get("SWAGGER_FILE", file_config.get('swagger_file', f"{pathlib.Path().absolute()}/swagger.yml" ))
    COPY_URI_DROPDOWN = os.environ.get("COPY_URI_DROPDOWN",
                          file_config.get('copy_uri_dropdown', "http://production-services.ensembl.org:80/"))
