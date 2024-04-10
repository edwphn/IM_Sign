# maintenance.py

""" Module for maintenance purpose. """
import os
import sys
from _logger import logger
from _config import DIR_TEMP
from _database import execute_sql_sync, create_Documents, create_DocumentsHistory
from _cert import check_certificate_validity, load_certificates_from_disk


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
    except Exception as e:
        logger.error(f"An error occurred while creating tables: {e}")


def check_certificates(first_attempt=True) -> None:
    valid_cert = check_certificate_validity()

    if not valid_cert:
        if not first_attempt:
            logger.critical('Couldn\'t load certificate from filesystem. Terminating program.')
            sys.exit(1)
        else:
            try:
                logger.info("Trying to load certificate from file system.")
                load_certificates_from_disk()
            except Exception as e:
                logger.critical(f"Failed to load certificates from filesystem: {e}")
                sys.exit(1)
            check_certificates(first_attempt=False)
    else:
        logger.success("Certificate is valid. Program can start now.")
