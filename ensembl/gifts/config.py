import os
from ensembl.config import EnsemblConfig
from ensembl_prodinf.config import load_config_yaml


config_file_path = os.environ.get('GIFTS_CONFIG_PATH')
file_config = load_config_yaml(config_file_path)

class GIFTsConfig(EnsemblConfig):
    BASE_DIR = os.environ.get('BASE_DIR',
                              file_config.get('base_dir'))
    HIVE_UPDATE_ENSEMBL_ANALYSIS = os.environ.get("HIVE_UPDATE_ENSEMBL_ANALYSIS",
                                                  file_config.get('hive_update_ensembl_analysis', 'submit'))
    HIVE_PROCESS_MAPPING_ANALYSIS = os.environ.get("HIVE_PROCESS_MAPPING_ANALYSIS",
                                                   file_config.get('hive_process_mapping_analysis', 'submit'))
    HIVE_PUBLISH_MAPPING_ANALYSIS = os.environ.get("HIVE_PUBLISH_MAPPING_ANALYSIS",
                                                   file_config.get('hive_publish_mapping_analysis', 'copy_database'))
    HIVE_UPDATE_ENSEMBL_URI = os.environ.get("HIVE_UPDATE_ENSEMBL_URI",
                                             file_config.get('hive_update_ensembl_uri', None))
    HIVE_PROCESS_MAPPING_URI = os.environ.get("HIVE_PROCESS_MAPPING_URI",
                                              file_config.get('hive_process_mapping_uri', None))
    HIVE_PUBLISH_MAPPING_URI = os.environ.get("HIVE_PUBLISH_MAPPING_URI",
                                              file_config.get('hive_publish_mapping_analysis', None))
    GIFTS_API_URIS_FILE = os.environ.get("GIFTS_APIS_URIS_FILE",
                                         file_config.get('gifts_api_uris_file', 'gifts_api_uris.json'))
    SWAGGER=EnsemblConfig.SWAGGER
    SWAGGER['title']='Ensembl Production: GIFTs Pipeline API'
    SWAGGER['favicon']='/img/gifts.png'
    SWAGGER['specs_route']='/gifts/api'
