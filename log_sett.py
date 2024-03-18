import sys
from loguru import logger

def setup_logger():
    logger.remove()
    logger.add(
        sys.stderr, format="{time} {level} {message}", level="INFO"
    )
    logger.add(
        "file.log", rotation="10 MB", format="{time} {level} {message}", level="DEBUG"
    )
