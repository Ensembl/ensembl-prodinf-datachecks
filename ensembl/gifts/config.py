import os
from ensembl.config import EnsemblConfig

class GIFTsConfig(EnsemblConfig):
  HIVE_UPDATE_ENSEMBL_ANALYSIS = os.environ.get("HIVE_UPDATE_ENSEMBL_ANALYSIS", 'submit')
  HIVE_PROCESS_MAPPING_ANALYSIS = os.environ.get("HIVE_PROCESS_MAPPING_ANALYSIS", 'submit')
  HIVE_PUBLISH_MAPPING_ANALYSIS = os.environ.get("HIVE_PUBLISH_MAPPING_ANALYSIS", 'copy_database')
  HIVE_UPDATE_ENSEMBL_URI = os.environ.get("HIVE_UPDATE_ENSEMBL_URI", None)
  HIVE_PROCESS_MAPPING_URI = os.environ.get("HIVE_PROCESS_MAPPING_URI", None)
  HIVE_PUBLISH_MAPPING_URI = os.environ.get("HIVE_PUBLISH_MAPPING_URI", None)
