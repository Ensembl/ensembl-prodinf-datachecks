import os
from ensembl_prodinf.config import load_yaml


config_file_path = os.environ.get('HANDOVER_CONFIG_PATH')
if config_file_path:
    file_config = load_yaml(config_file_path)
else:
    file_config = {}


DEBUG = str(os.environ.get("DEBUG", file_config.get('debug', 'false')))
if DEBUG.lower() in ("f", "false"):
    DEBUG = False
elif DEBUG.lower() in ("t", "true"):
    DEBUG = True

HOST = os.environ.get('SERVICE_HOST', file_config.get('host', '0.0.0.0'))
PORT = os.environ.get('SERVICE_PORT', file_config.get('port'))
ES_HOST = os.environ.get('ES_HOST', file_config.get('es_host', 'localhost'))
ES_PORT = os.environ.get('ES_PORT', file_config.get('es_port', '9200'))
RELEASE = os.environ.get('ENS_RELEASE', file_config.get('ens_release', '99'))
