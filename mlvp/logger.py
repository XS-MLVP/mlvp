import logging

class StatsHandler(logging.Handler):
    """Provides quantity statistics based on severity and id """

    def __init__(self):
        logging.Handler.__init__(self)
        self.serverity_stats = {}
        self.id_stats = {}

    def emit(self, record):
        # Count the number of logs based on severity and id

        if record.levelname not in self.serverity_stats:
            self.serverity_stats[record.levelname] = 0
        self.serverity_stats[record.levelname] += 1

        log_id = record.__dict__.get('log_id', 'default_id')
        if log_id == '':
            log_id = 'default'
        if log_id not in self.id_stats:
            self.id_stats[log_id] = 0
        self.id_stats[log_id] += 1

    def get_stats(self):
        return self.stats

# MLVP Global Logger
logger = logging.getLogger("MLVP")
stats_handler = StatsHandler()
screen_handler = logging.StreamHandler()

# Default Formatter
default_format = '%(name)s_%(levelname)s @%(filename)s:%(lineno)d%(log_id)s:\t%(message)s'
class MLVPFormatter(logging.Formatter):
    def format(self, record):
        if not hasattr(record, 'log_id'):
            record.log_id = ''
        else:
            record.log_id = f"(id: {record.log_id})"
        return super().format(record)

default_formatter = MLVPFormatter(default_format)


def setup_logging(log_level=logging.INFO, format=default_format, log_file=None):
    logging.basicConfig(level=log_level, format=format, handlers=[])

    screen_handler.setLevel(log_level)
    screen_handler.setFormatter(default_formatter)
    logger.addHandler(screen_handler)

    logger.setLevel(log_level)
    logger.addHandler(stats_handler)

    if log_file:
        fh = logging.FileHandler(log_file, mode='w')
        fh.setLevel(log_level)
        fh.setFormatter(default_formatter)
        logger.addHandler(fh)

    return logger

def summary():
    summary_str = "Log Summary\n"
    summary_str += "============\n"
    summary_str += "* Report counts by severity\n"
    for k, v in stats_handler.serverity_stats.items():
        summary_str += f"{k}:\t{v}\n"
    summary_str += "* Report counts by id\n"
    for k, v in stats_handler.id_stats.items():
        summary_str += f"{k}:\t{v}\n"

    logger.info(summary_str)

setup_logging()
