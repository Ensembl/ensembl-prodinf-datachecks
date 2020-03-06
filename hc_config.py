import os
from ensembl_prodinf.config import load_config_yaml, parse_debug_var


config_file_path = os.environ.get('HC_CONFIG_PATH')
file_config = load_config_yaml(config_file_path)


debug_var = os.environ.get("DEBUG", file_config.get('debug', 'false'))

DEBUG = parse_debug_var(debug_var)

HIVE_ANALYSIS = os.environ.get("HIVE_ANALYSIS",
                               file_config.get('hive_analysis', 'RunStandaloneHealthcheckFactory'))
HIVE_URI = os.environ.get("HIVE_URI", file_config.get('hive_uri'))
HC_LIST_FILE = os.environ.get("HC_LIST_FILE",
                              file_config.get('hc_list_file', './hc_list.json'))
HC_GROUPS_FILE = os.environ.get("HC_GROUPS_FILE",
                                file_config.get('hc_groups_file', './hc_groups.json'))
HOST = os.environ.get('SERVICE_HOST', file_config.get('service_host', '0.0.0.0'))
PORT = os.environ.get('SERVICE_PORT', file_config.get('service_port', '5001'))

