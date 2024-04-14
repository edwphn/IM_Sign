# _logger.py

import json
import logging.config


def get_logging_config():
    with open('logging_config.json', 'r') as config_file:
        return json.load(config_file)


logging_config = get_logging_config()
logging.config.dictConfig(logging_config)


def setup_logger():
    return logging.getLogger(__name__)


logger = setup_logger()
