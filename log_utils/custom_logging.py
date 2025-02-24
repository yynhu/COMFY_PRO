import logging
import os
from logging.handlers import RotatingFileHandler


class CustomLogging:
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, name, file_path=None, flash=False):
        if not self._initialized:
            self.logger = logging.getLogger(name)
            if flash:
                if os.path.exists(file_path):
                    os.remove(file_path)
            file_handler = RotatingFileHandler(file_path, mode='a', maxBytes=5 * 1024 * 1024, backupCount=10, encoding='utf-8', delay=True)
            formatter = logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            self.logger.setLevel(logging.DEBUG)
            self._initialized = True

    def debug(self, message):
        self.logger.debug(message)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def critical(self, message):
        self.logger.critical(message)
