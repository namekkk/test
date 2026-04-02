# logging_config.py
import logging

def setup_logging():
    logging.basicConfig(
        filename='add_users.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        encoding='utf-8'
    )