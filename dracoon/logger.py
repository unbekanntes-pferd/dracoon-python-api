import logging

def create_logger(log_file: str, log_level: int):

    logger = logging.getLogger('dracoon')
    stream_handler = logging.StreamHandler()
    file_handler = logging.FileHandler(filename=log_file)
    formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)
    logger.setLevel(log_level)
    
    return logger