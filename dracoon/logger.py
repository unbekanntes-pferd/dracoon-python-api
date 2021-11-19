import logging

def create_logger(log_file: str, log_level: int, log_stream: bool):

    logger = logging.getLogger('dracoon')

    formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')

    if log_stream:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
        
    file_handler = logging.FileHandler(filename=log_file)
    
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.setLevel(log_level)
    
    return logger