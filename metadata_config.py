import os
from ensembl_prodinf.config import load_yaml


config_file_path = os.environ.get('METADATA_CONFIG_PATH')
if config_file_path:
    file_config = load_yaml(config_file_path)
else:
    file_config = {}


DEBUG = str(os.environ.get("DEBUG", file_config.get('debug', 'false')))
if DEBUG.lower() in ("f", "false"):
    DEBUG = False
elif DEBUG.lower() in ("t", "true"):
    DEBUG = True

HIVE_ANALYSIS = os.environ.get("HIVE_ANALYSIS",
                               file_config.get('hive_analysis', 'metadata_updater_processdb'))
HIVE_URI = os.environ.get("HIVE_URI", file_config.get('hive_uri'))
METADATA_URI = os.environ.get("METADATA_URI", file_config.get('metadata_uri'))
HOST = os.environ.get('SERVICE_HOST', file_config.get('service_host', '0.0.0.0'))
PORT = os.environ.get('SERVICE_PORT', file_config.get('service_port', '5003'))
