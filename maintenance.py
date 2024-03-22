# maintenance.py

"""Module for maintanance purpose."""
import os
import datetime
import sys
from config_loader import config_vars
from log_sett import logger
from _certificate import check_certificate_validity, load_certificates_from_disk


def maintenance(first_attempt=True) -> None:
    logger.info("Initializing maintenance") if first_attempt else None

    valid_cert = check_certificate_validity()

    if not valid_cert:
        logger.error("No valid certificate in database.")
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
            maintenance(first_attempt=False)
    else:
        logger.success("Certificate is valid. Program can start now.")


maintenance()
