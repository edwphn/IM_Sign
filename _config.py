# _config.py

import os
import sys
import configparser
from _logger import logger


logger.info('Loading configuration settings.')
config = configparser.ConfigParser()
CONFIG_FILE = 'config.ini'

if not os.path.exists(CONFIG_FILE):
    logger.critical(f"Configuration file '{CONFIG_FILE}' not found.")
    sys.exit(1)

try:
    config.read(CONFIG_FILE)
except configparser.Error as e:
    logger.critical(f"Error reading configuration file: {e}")
    sys.exit(1)

try:
    DIR_CERTIFICATE = config['DIRECTORIES']['CERTIFICATE']
    DIR_TEMP = config['DIRECTORIES']['temp_folder']
    DB_SERVER_URL = config['DATABASE']['DB_SERVER']
    DB_NAME = config['DATABASE']['DB_NAME']
    DB_USER = config['DATABASE']['DB_USER']
    DB_PASSWORD = config['DATABASE']['DB_PASSWORD']
    ENCRYPTION_KEY = config['CERT']['ENCRYPTION_KEY']
    CERTIFICATES = config['CERT']['CERTIFICATES']
    KTA_API_URL = config['KTA']['URL']
except (KeyError, ValueError) as e:
    logger.critical(f"Error setting configuration variables: {e}")
    sys.exit(1)


logger.success('Settings have been loaded.')
