import os
from ensembl_prodinf.config import load_config_yaml, parse_debug_var


config_file_path = os.environ.get('LOCK_CONFIG_PATH')
file_config = load_config_yaml(config_file_path)


debug_var = os.environ.get("DEBUG", file_config.get('debug', 'false'))

DEBUG = parse_debug_var(debug_var)

LOCK_URI = os.environ.get("LOCK_URI", file_config.get('lock_uri'))

