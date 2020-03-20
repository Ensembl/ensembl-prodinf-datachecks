import os
from ensembl.config import EnsemblConfig
from ensembl_prodinf.config import load_config_yaml


config_file_path = os.environ.get('DATACHECK_CONFIG_PATH')
file_config = load_config_yaml(config_file_path)


class DatacheckConfig(EnsemblConfig):
    DATACHECK_INDEX = os.path.join(EnsemblConfig.BASE_DIR, 'ensembl-datacheck/lib/Bio/EnsEMBL/DataCheck/index.json')
    DATACHECK_COMMON_DIR = os.environ.get("DATACHECK_COMMON_DIR",
                                          file_config.get('datacheck_common_dir'))
    DATACHECK_CONFIG_DIR = os.path.join(DATACHECK_COMMON_DIR, 'config')
    DATACHECK_REGISTRY_DIR = os.path.join(DATACHECK_COMMON_DIR, 'registry')
    DATACHECK_REGISTRY_META = os.path.join(DATACHECK_REGISTRY_DIR, 'registry_meta.pm')
    HIVE_ANALYSIS = os.environ.get("HIVE_ANALYSIS",
                                   file_config.get('hive_analysis', 'DataCheckSubmission'))
    HIVE_VERT_URI = os.environ.get("HIVE_VERT_URI", file_config.get('hive_vert_uri'))
    HIVE_NONVERT_URI = os.environ.get("HIVE_NONVERT_URI", file_config.get('hive_nonvert_uri'))
