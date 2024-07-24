import logging
from logging.handlers import BaseRotatingHandler
import os
import requests
import datetime
import colorlog
from app.config import Config

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

class CustomFileHandler(BaseRotatingHandler):
    def __init__(self, filename, maxBytes=0, encoding=None, delay=False):
        self.maxBytes = maxBytes
        self.baseFilename = filename
        super().__init__(filename, 'a', encoding, delay)
        self.stream = self._open()  # Open the stream when initializing
        logging.debug(f"CustomFileHandler initialized with file: {self.baseFilename}")

    def shouldRollover(self, record):
        logging.debug("Checking if rollover is needed")
        if self.maxBytes > 0:  # Are we rolling over?
            if self.stream is None:
                logging.debug("Stream is None, opening stream")
                self.stream = self._open()  # Ensure the stream is opened
            self.stream.seek(0, 2)  # Due to non-posix-compliant Windows feature
            if self.stream.tell() + len(self.format(record)) >= self.maxBytes:
                logging.debug("Rollover needed")
                return 1
        return 0

    def doRollover(self):
        logging.debug("Performing rollover")
        if self.stream:
            self.stream.close()
            self.stream = None

        self.baseFilename = self.get_new_log_file()
        self.mode = 'a'
        self.stream = self._open()
        logging.debug(f"Rolled over to new file: {self.baseFilename}")

    def get_new_log_file(self):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{self.baseFilename}_{timestamp}.log"

    def get_latest_log_file(self):
        log_dir = os.path.dirname(self.baseFilename)
        log_files = sorted(
            [f for f in os.listdir(log_dir) if f.startswith(os.path.basename(self.baseFilename))],
            reverse=True
        )
        if log_files:
            latest_log_file = os.path.join(log_dir, log_files[0])
            if os.path.getsize(latest_log_file) < self.maxBytes:
                return latest_log_file
        
        return self.get_new_log_file()

def setup_logger():
    logger = logging.getLogger('discord_bot')
    logger.setLevel(logging.DEBUG)

    # Ensure the log directory exists
    log_dir = os.path.dirname(Config.LOG_FILE_PATH)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        logging.debug(f"Created log directory: {log_dir}")

    # Custom File handler with utf-8 encoding
    file_handler = CustomFileHandler(Config.LOG_FILE_PATH, maxBytes=1024*1024*0.5, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))

    # Stream handler (console) with color
    console_handler = colorlog.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(colorlog.ColoredFormatter(
        '%(log_color)s%(levelname)s: %(message)s',
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
