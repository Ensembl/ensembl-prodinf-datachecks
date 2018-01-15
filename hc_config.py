import os
DEBUG = os.environ.get("DEBUG", 'false')
if DEBUG.lower() in ("f", "false"):
    DEBUG = False
elif DEBUG.lower() in ("t", "true"):
    DEBUG = True

HIVE_ANALYSIS = os.environ.get("HIVE_ANALYSIS", 'RunStandaloneHealthcheckFactory')
HIVE_URI = os.environ.get("HIVE_URI", None)

