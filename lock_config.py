import os
DEBUG = os.environ.get("DEBUG", 'false')
if DEBUG.lower() in ("f", "false"):
    DEBUG = False
elif DEBUG.lower() in ("t", "true"):
    DEBUG = True

LOCK_URI = os.environ.get("LOCK_URI", None)

