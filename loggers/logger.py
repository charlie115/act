import logging

class KimpBotLogger:
    def __init__(self, logger_name, logging_dir=''):
        self.logger_name = logger_name
        logging.Formatter(
            fmt = None,
            datefmt = None,
            style = '%'
        )
        formatter = logging.Formatter(fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        stream_handler = logging.StreamHandler()
        file_handler = logging.FileHandler(filename=f'{logging_dir}{self.logger_name}.log')
        stream_handler.setLevel(logging.DEBUG)
        stream_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger = logging.getLogger(self.logger_name)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(stream_handler)
        logger.addHandler(file_handler)
        self.logger = logger