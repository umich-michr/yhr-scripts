import logging.config
import yaml
import os

def configure_logging():
    logging_config_file = os.path.join(os.path.dirname(__file__), 'logger.yaml')
    with open(logging_config_file, 'r') as f:
        logging_config = yaml.safe_load(f)
    logging.config.dictConfig(logging_config)