import logging
from logging.handlers import RotatingFileHandler
import requests
from app.config import Config
import datetime
import colorlog

class LokiHandler(logging.Handler):
    def __init__(self, url):
        super().__init__()
        self.url = url

    def emit(self, record):
        log_entry = self.format(record)
        payload = {
            "streams": [
                {
                    "labels": "{job=\"discord_bot\"}",
                    "entries": [{"ts": self.format_time(record.created), "line": log_entry}]
                }
            ]
        }
        try:
            requests.post(self.url + '/loki/api/v1/push', json=payload)
        except Exception as e:
            print(f"Failed to send log to Loki: {e}")

    def format_time(self, timestamp):
        return datetime.datetime.fromtimestamp(timestamp, datetime.timezone.utc).isoformat()

def setup_logger():
    logger = logging.getLogger('discord_bot')
    logger.setLevel(logging.DEBUG)

    # File handler
    file_handler = RotatingFileHandler(Config.LOG_FILE_PATH, maxBytes=1024*1024*5, backupCount=2)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))

    # Stream handler (console) with color
    console_handler = colorlog.StreamHandler()  
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(colorlog.ColoredFormatter(
        '%(log_color)s%(levelname)s: %(message)s',  # Removed '%(asctime)s:' and '%(name)s:'
        log_colors={
            'DEBUG': 'green',
            'INFO': 'light_blue', 
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold_red',
        }
    ))

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

logger = setup_logger()
