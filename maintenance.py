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
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta, timezone


async def delete_old_files():
    """
    Asynchronously deletes files older than 5 days from a specified directory,
    excluding files that start with a dot (hidden files).

    This function scans through the directory specified by DIR_TEMP, checks each file to determine
    if it is older than 5 days using the file creation timestamp. Files that start with a dot are
    ignored to prevent deletion of system or hidden files. If a file meets the criteria, it is deleted.

    Exceptions for file deletion errors (e.g., PermissionError, FileNotFoundError) are caught and
    logged as errors. Successful deletions are logged as informational messages.

    Uses:
        - `os`: To list files in the directory and to delete files.
        - `datetime`: To calculate the age of files and to ensure all time calculations are in UTC.
        - `logging`: To log information and errors related to file deletion.

    Note:
        - The function assumes that the file creation time can be retrieved accurately across
          different operating systems.
        - The function runs asynchronously and should be handled within an async event loop.
    """
    now = datetime.now(timezone.utc)
    threshold = timedelta(days=5)

    for filename in os.listdir(DIR_TEMP):
        file_path = os.path.join(DIR_TEMP, filename)
        if os.path.isfile(file_path) and not filename.startswith('.'):
            file_creation_time = datetime.fromtimestamp(os.path.getctime(file_path), timezone.utc)
            if now - file_creation_time > threshold:
                try:
                    os.remove(file_path)
                except (PermissionError, FileNotFoundError) as e:
                    logger.error(f"Problem with deleting file {file_path}: {e}")
                else:
                    logger.info(f"File {file_path} has been removed from disk after transmission.")


scheduler = AsyncIOScheduler()
scheduler.add_job(delete_old_files, 'interval', days=1)
scheduler.start()


def start_scheduler():
    if not scheduler.running:
        scheduler.start()


def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown()


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
