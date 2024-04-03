import logging

log_counter = {'DEBUG': 0, 'INFO': 0, 'WARNING': 0, 'ERROR': 0, 'CRITICAL': 0}

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
def count_logs(record):
    log_counter[record.levelname] += 1

logging.getLogger().addHandler(logging.StreamHandler())
logging.getLogger().handlers[-1].setLevel(logging.INFO)
logging.getLogger().handlers[-1].addFilter(count_logs)

def debug(msg):
    logging.debug(msg)

def info(msg):
    logging.info(msg)

def warning(msg):
    logging.warning(msg)

def error(msg):
    logging.error(msg)

def critical(msg):
    logging.critical(msg)

def get_log_counter():
    return log_counter
