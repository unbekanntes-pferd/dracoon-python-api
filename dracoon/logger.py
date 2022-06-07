from logging import Logger, StreamHandler, FileHandler, Formatter, getLogger

def create_logger(log_level: int, log_stream: bool, log_file_out: bool = False, log_file: str = None) -> Logger:

    logger = getLogger('dracoon')

    formatter = Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')

    if log_stream:
        stream_handler = StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
        
    if log_file_out and log_file is not None:
        file_handler = FileHandler(filename=log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    logger.setLevel(log_level)
    
    return logger