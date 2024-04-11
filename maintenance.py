# maintenance.py

""" Module for maintenance purpose. """
import os
import sys
from _logger import logger
from _config import DIR_TEMP
from _database import execute_sql_sync, create_Documents, create_DocumentsHistory, create_Certificates
from _cert import Certificate, certs
from _config import CERTIFICATES


def check_directories() -> None:
    if not DIR_TEMP:
        logger.critical('Missing temporary folder in config.')
        sys.exit(1)
    else:
        if not os.path.exists(DIR_TEMP):
            os.makedirs(DIR_TEMP)
            logger.info('Temporary directory created.')
        else:
            logger.info('Temporary directory found.')


def create_tables() -> None:
    logger.info('Checking database table existence.')
    try:
        execute_sql_sync(create_Documents)
        execute_sql_sync(create_DocumentsHistory)
        execute_sql_sync(create_Certificates)
    except Exception as e:
        logger.error(f"An error occurred while creating tables: {e}")


def check_certificates() -> None:
    cfg_certs = {name: Certificate(name) for name in CERTIFICATES.split(',')}
    certs.update(cfg_certs)

