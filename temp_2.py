# Read configuration
try:
    config.read(CONFIG_FILE)
except configparser.Error as e:
    logger.error(f"Error reading configuration file: {e}")
    sys.exit(1)
