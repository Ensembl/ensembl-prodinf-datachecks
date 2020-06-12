import yaml
import json
import logging


logger = logging.getLogger(__name__)


def load_config_yaml(file_path, strict=False):
    if file_path:
        with open(file_path, 'r') as f:
            config = yaml.safe_load(f)
        return config if config else {}
    else:
        if strict:
            raise ValueError('Invalid config file path: %s' % file_path)
        else:
            logger.warning('Using default configuration. Config file path was: %s' % file_path)
            return {}


def parse_debug_var(var):
    return not ((str(var).lower() in ('f', 'false', 'no', 'none')) or (not var))


def load_config_json(file_path):
    with open(file_path, 'r') as f:
        config = json.load(f)
    return config if config else {}

