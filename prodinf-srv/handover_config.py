import os
from ensembl_prodinf.config import load_config_yaml, parse_debug_var


config_file_path = os.environ.get('HANDOVER_CONFIG_PATH')
file_config = load_config_yaml(config_file_path)


debug_var = os.environ.get("DEBUG", file_config.get('debug', 'false'))

DEBUG = parse_debug_var(debug_var)

HOST = os.environ.get('SERVICE_HOST', file_config.get('host', '0.0.0.0'))
PORT = os.environ.get('SERVICE_PORT', file_config.get('port'))
ES_HOST = os.environ.get('ES_HOST', file_config.get('es_host', 'localhost'))
ES_PORT = os.environ.get('ES_PORT', file_config.get('es_port', '9200'))
ES_INDEX = os.environ.get('ES_INDEX', file_config.get('es_index', 'reports'))
RELEASE = os.environ.get('ENS_RELEASE', file_config.get('ens_release', '99'))
