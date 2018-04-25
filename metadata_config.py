import os

DEBUG = os.environ.get("DEBUG", 'false')
if DEBUG.lower() in ("f", "false"):
    DEBUG = False
elif DEBUG.lower() in ("t", "true"):
    DEBUG = True

HIVE_ANALYSIS = os.environ.get("HIVE_ANALYSIS", 'metadata_updater_processdb')
HIVE_URI = os.environ.get("HIVE_URI", None)
METADATA_URI = os.environ.get("METADATA_URI", None)