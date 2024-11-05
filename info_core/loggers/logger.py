import logging
from logging.handlers import TimedRotatingFileHandler
import time
from datetime import datetime, timedelta
import os

class MonthlyRotatingFileHandler(TimedRotatingFileHandler):
    def __init__(self, filename, backupCount=0, encoding=None, delay=False, utc=False):
        super().__init__(filename, when='midnight', interval=1, backupCount=backupCount, encoding=encoding, delay=delay, utc=utc)
        self.suffix = "%Y-%m"
        self.extMatch = r"^\d{4}-\d{2}$"

    def shouldRollover(self, record):
        """
        Determine if rollover should occur.

        Basically, see if the month has changed since the last rollover.
        """
        t = int(self.rolloverAt - self.interval)
        if self.utc:
            current_time = datetime.utcnow()
        else:
            current_time = datetime.now()

        # Check if the month has changed
        if current_time.month != time.localtime(t)[1]:
            return True
        return False

    def getFilesToDelete(self):
        """
        Determine the files to delete when rolling over.

        Overrides the base method to match files with the monthly suffix.
        """
        dirName, baseName = os.path.split(self.baseFilename)
        fileNames = os.listdir(dirName)
        result = []
        prefix = baseName + "."
        plen = len(prefix)
        for fileName in fileNames:
            if fileName[:plen] == prefix:
                suffix = fileName[plen:]
                if self.extMatch.match(suffix):
                    result.append(os.path.join(dirName, fileName))
        result.sort()
        if len(result) < self.backupCount:
            result = []
        else:
            result = result[:len(result) - self.backupCount]
        return result

class InfoCoreLogger:
    def __init__(self, logger_name, logging_dir=''):
        self.logger_name = logger_name
        logging.Formatter(
            fmt = None,
            datefmt = None,
            style = '%'
        )
        # Formatter
        formatter = logging.Formatter(fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        
        # Stream handler for console output
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.DEBUG)
        stream_handler.setFormatter(formatter)
        
        # Timed rotating file handler for monthly log rotation
        file_handler = MonthlyRotatingFileHandler(
        filename=f'{logging_dir}{self.logger_name}.log',
        backupCount=6,     # Keep last 6 months of logs
        encoding='utf-8'
)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)

        # Logger setup
        logger = logging.getLogger(self.logger_name)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(stream_handler)
        logger.addHandler(file_handler)

        self.logger = logger