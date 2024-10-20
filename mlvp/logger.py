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

# ANSI escape sequences for colors
RESET = "\x1b[0m"
YELLOW = "\x1b[33m"
RED = "\x1b[31m"
GREEN = "\x1b[32m"
BLUE = "\x1b[34m"
WHITE = "\x1b[37m"

class MLVPFormatter(logging.Formatter):
    """
    Custom formatter for MLVP logs. It supports log_id attribute display in the log record
    """

    def format(self, record):
        if not hasattr(record, 'log_id') or record.log_id == '':
            record.log_id = ''
        else:
            record.log_id = f"(id: {record.log_id})"

        log_colors = {
            'DEBUG': BLUE,
            'INFO': WHITE,
            'WARNING': YELLOW,
            'ERROR': RED,
            'CRITICAL': RED
        }

        color = log_colors.get(record.levelname, WHITE)
        message = super().format(record)
        return f"{color}{message}{RESET}"


#####################################
# MLVP Global Logging Configuration #
#####################################

mlvp_logger = logging.getLogger("MLVP")

def get_logger() -> logging.Logger:
    """Returns the global logger for MLVP"""

    return mlvp_logger


# Global handlers
# stats_handler is used to collect statistics about the logs
stats_handler = StatsHandler()
# screen_handler is used to display logs on the screen
screen_handler = logging.StreamHandler()


# Default format and formatter
default_format = '%(name)s_%(levelname)s @%(filename)s:%(lineno)d%(log_id)s:\t%(message)s'
default_formatter = MLVPFormatter(default_format)

# log levels
INFO = logging.INFO
DEBUG = logging.DEBUG
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL

def setup_logging(log_level=WARNING, format=default_format, console_display=True, log_file=None):
    """
    Setup the logging configuration for MLVP

    Args:
        log_level: The log level for the logger
        format: The format of the log message
        console_display: Whether to display logs on the console
        log_file: The log file name to write logs, if None, logs are not written to a file
    """

    logging.basicConfig(level=log_level, format=format, handlers=[])
    mlvp_logger.setLevel(log_level)

    for handler in mlvp_logger.handlers[:]:
        mlvp_logger.removeHandler(handler)
        handler.close()

    mlvp_logger.addHandler(stats_handler)

    if console_display:
        screen_handler.setLevel(log_level)
        screen_handler.setFormatter(default_formatter)
        mlvp_logger.addHandler(screen_handler)

    if log_file:
        fh = logging.FileHandler(log_file, mode='w')
        fh.setLevel(log_level)
        fh.setFormatter(default_formatter)
        mlvp_logger.addHandler(fh)

setup_logging()

##########################
# MLVP Logging Functions #
##########################

log = mlvp_logger.log
debug = mlvp_logger.debug
info = mlvp_logger.info
warning = mlvp_logger.warning
error = mlvp_logger.error
critical = mlvp_logger.critical
exception = mlvp_logger.exception

def summary():
    """Display a summary of the logs"""

    summary_str = "Log Summary\n"
    summary_str += "============\n"
    summary_str += "* Report counts by severity\n"
    for k, v in stats_handler.serverity_stats.items():
        summary_str += f"{k}:\t{v}\n"
    # summary_str += "* Report counts by id\n"
    # for k, v in stats_handler.id_stats.items():
    #     summary_str += f"{k}:\t{v}\n"

    mlvp_logger.info(summary_str)
