import os

class EnsemblConfig:
  BASE_DIR = os.environ.get('BASE_DIR', None)
  SECRET_KEY = os.environ.get('SECRET_KEY', os.urandom(32))
  SERVER_URIS_FILE = 'ensembl/server_uris_list.json'
  SWAGGER = {
    'title': 'Ensembl Production Web Services',
    'uiversion': 3,
    'hide_top_bar': True,
    'ui_params': {
      'defaultModelsExpandDepth': -1
    },
    'favicon': '/img/production.png'
  }
