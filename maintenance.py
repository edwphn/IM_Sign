# maintenance.py

""" Module for maintenance purposes in a FastAPI application.
This module includes functionalities to check directories, create database tables,
and verify certificates based on configuration settings.
"""

import os
import sys
from _logger import logger
from _config import DIR_TEMP
from _database import execute_sql_sync, create_Documents, create_DocumentsHistory, create_Certificates
from _cert import Certificate, CERTS
from _config import CERTIFICATES


def check_directories() -> None:
    """Checks for the existence of the temporary directory specified in the configuration.
    Creates the directory if it does not exist and logs the activity.

    Raises:
        SystemExit: If the DIR_TEMP is not defined in the configuration.
    """
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
    """Attempts to create necessary database tables by executing SQL commands.
    Logs information about the process and errors if any occur.

    Catches and logs exceptions that might occur during the database operations.
    """
    logger.info('Checking database table existence.')
    try:
        execute_sql_sync(create_Documents)
        execute_sql_sync(create_DocumentsHistory)
        execute_sql_sync(create_Certificates)
    except Exception as e:
        logger.error(f"An error occurred while creating tables: {e}")


def check_certificates() -> None:
    """Parses certificate data from configuration and initializes certificate objects.
    Updates the global certificate registry with these objects.

    Logs errors if the certificate data is improperly formatted or missing.
    """
    certs = CERTIFICATES.strip(',').split(',')
    cfg_certs = {}

    for cert in certs:
        if cert.strip():
            cert = cert.split(' ')
            if len(cert) == 2:
                name, pwd = cert
                cfg_certs[name] = Certificate(name, pwd)
            elif len(cert) == 1:
                name = cert[0]
                cfg_certs[name] = Certificate(name)
            else:
                logger.error(f"Error parsing certificate data: '{cert}'")

    if cfg_certs:
        CERTS.update(cfg_certs)
    else:
        logger.error("No valid certificates data found in config.ini")
