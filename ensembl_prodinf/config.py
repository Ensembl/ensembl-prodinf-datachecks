import yaml
import logging


logger = logging.getLogger(__name__)


def load_config_yaml(file_path, strict=False):
    if file_path:
        with open(file_path, 'r') as f:
            config = yaml.safe_load(f)
        return config if config else {}
    else:
        if strict:
            raise ValueError('Invalid config file path: {}'.format(file_path))
        else:
            logger.warning('Using default configuration. Config file path was: {}'.format(file_path))
            return {}


def parse_debug_var(var):
    if (str(var).lower() in ('f', 'false', 'no', 'none')) or (not var):
        return False
    else:
        return True

