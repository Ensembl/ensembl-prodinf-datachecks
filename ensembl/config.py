import os
from ensembl_prodinf.config import load_yaml


config_file_path = os.environ.get('DATACHECK_CONFIG_PATH')
if config_file_path:
    file_config = load_yaml(config_file_path)
else:
    file_config = {}


class EnsemblConfig:
    BASE_DIR = os.environ.get('BASE_DIR',
                              file_config.get('base_dir'))
    SECRET_KEY = os.environ.get('SECRET_KEY',
                                file_config.get('secret_key', os.urandom(32)))
    SERVER_URIS_FILE = os.environ.get('SERVER_URIS_FILE',
                                      file_config.get('server_uris_file', 'ensembl/server_uris_list.json'))
    SWAGGER = {
      'title': 'Ensembl Production Web Services',
      'uiversion': 3,
      'hide_top_bar': True,
      'ui_params': {
        'defaultModelsExpandDepth': -1
      },
      'favicon': '/img/production.png'
    }
