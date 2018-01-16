import os

DEBUG = os.environ.get("DEBUG", 'false')
if DEBUG.lower() in ("f", "false"):
    DEBUG = False
elif DEBUG.lower() in ("t", "true"):
    DEBUG = True

HIVE_ANALYSIS = os.environ.get("HIVE_ANALYSIS", 'copy_database')
HIVE_URI = os.environ.get("HIVE_URI", None)

SERVER_URIS_FILE = os.environ.get("SERVER_URIS_FILE", 'server_uris.json')
