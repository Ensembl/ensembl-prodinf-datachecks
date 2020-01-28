import os
from ensembl_prodinf.config import load_yaml


config_file_path = os.environ.get('LOCK_CONFIG_PATH')
if config_file_path:
    file_config = load_yaml(config_file_path)
else:
    file_config = {}


DEBUG = str(os.environ.get("DEBUG", file_config.get('debug', 'false')))
if DEBUG.lower() in ("f", "false"):
    DEBUG = False
elif DEBUG.lower() in ("t", "true"):
    DEBUG = True

LOCK_URI = os.environ.get("LOCK_URI", file_config.get('lock_uri'))

