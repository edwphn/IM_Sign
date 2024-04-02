# log_sett.py

import sys
from loguru import logger

def setup_logger():
    logger.remove()
    logger.add(
        sys.stderr,
        format="{time:YYYY-MM-DD HH:mm:ss} {level} {file}:{line} {message}",
        level="INFO"
    )
    logger.add(
        "file.log",
        rotation="10 MB",
        format="{time:YYYY-MM-DD HH:mm:ss} {level} {file}:{line} {message}",
        level="DEBUG"
    )


setup_logger()
