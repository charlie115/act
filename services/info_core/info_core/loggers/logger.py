import logging
from logging.handlers import TimedRotatingFileHandler
import time
from datetime import datetime, timedelta
import os
import fcntl
import multiprocessing

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
    _mp_lock = multiprocessing.Lock()
    
    def __init__(self, logger_name, logging_dir=''):
        self.logger_name = logger_name  # Remove PID from name
        self.logging_dir = logging_dir
        self.logger = self._get_logger()
    
    def _get_logger(self):
        with InfoCoreLogger._mp_lock:
            logger = logging.getLogger(self.logger_name)
            
            if logger.handlers:
                return logger
                
            logger.setLevel(logging.INFO)
            
            # Keep PID in log format
            formatter = logging.Formatter(
                fmt="%(asctime)s - %(name)s - [PID:%(process)d] - %(levelname)s - %(message)s"
            )
            
            # Console handler
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(formatter)
            logger.addHandler(stream_handler)
            
            # File handler with locking
            log_file = f'{self.logging_dir}{self.logger_name}.log'
            file_handler = MonthlyRotatingFileHandler(
                filename=log_file,
                backupCount=6,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            
            # Add file locking
            original_emit = file_handler.emit
            def emit_with_lock(record):
                with open(log_file, 'a') as f:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                    try:
                        original_emit(record)
                    finally:
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            file_handler.emit = emit_with_lock
            
            logger.addHandler(file_handler)
            return logger