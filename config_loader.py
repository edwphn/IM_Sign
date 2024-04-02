# config_handler.py

import configparser
import os
import sys
from typing import Any, Dict
from log_sett import logger


logger.info('Loading configuration settings.')

# Script directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Config file
CONFIG_FILE = 'config.ini'
# Check if config file exists
if not os.path.exists(CONFIG_FILE):
    logger.error(f"Configuration file '{CONFIG_FILE}' not found.")
    sys.exit(1)

try:
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)

except (FileExistsError, TypeError) as e:
    logger.error(f"Error reading configuration file: {e}")
    sys.exit(1)

# Set up variables from config
try:
    config_vars: Dict[str, Dict[str, Any]] = {
        'DIRECTORIES': {
            'CERTIFICATE': config['DIRECTORIES']['CERTIFICATE'],
            'TEMP': config['DIRECTORIES']['temp_folder']
        },
        'DATABASE': {
            'SERVER': config['DATABASE']['DB_SERVER'],
            'NAME': config['DATABASE']['DB_NAME'],
            'USER': config['DATABASE']['DB_USER'],
            'PASSWORD': config['DATABASE']['DB_PASSWORD']
        },
        'ENCRYPTION': {
            'KEY': config['ENCRYPTION']['KEY']
        },
        'KTA': {
            'api_url': config['KTA']['URL']
        }
    }

except KeyError as e:
    logger.error(f"Error setting configuration variables: {e}")
    raise Exception(f"Error setting configuration variables: {e}")


logger.success('Settings have been loaded.')
