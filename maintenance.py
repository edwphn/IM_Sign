# maintenance.py

"""Module for maintenance purpose."""
import os
import sys
from config_loader import config_vars, SCRIPT_DIR
from log_sett import logger
from _certificate import check_certificate_validity, load_certificates_from_disk


def check_directories() -> None:
    file_directory = SCRIPT_DIR + config_vars["DIRECTORIES"]["TEMP"]
    if not os.path.exists(file_directory):
        os.makedirs(file_directory)
        logger.info("Temporary directory created.")
    else:
        logger.info("Temporary folder found.")


def check_certificate(first_attempt=True) -> None:
    valid_cert = check_certificate_validity()

    if not valid_cert:
        if not first_attempt:
            logger.critical("Couldn't load certificate from filesystem. Terminating program.")
            sys.exit(1)
        else:
            try:
                logger.info("Trying to load certificate from file system.")
                load_certificates_from_disk()
            except Exception as e:
                logger.critical(f"Failed to load certificates from filesystem: {e}")
                sys.exit(1)
            check_certificate(first_attempt=False)
    else:
        logger.success("Certificate is valid. Program can start now.")


def init_maintenance() -> None:
    logger.info("Initializing maintenance.")
    check_certificate()
    check_directories()
