import logging

__all__ = [
    "get_logger",
    "setup_logging",
    "INFO",
    "DEBUG",
    "WARNING",
    "ERROR",
    "CRITICAL",
    "log",
    "debug",
    "info",
    "warning",
    "error",
    "critical",
    "exception",
    "summary",
]


class StatsHandler(logging.Handler):
    """Provides quantity statistics based on severity and id"""

    def __init__(self):
        logging.Handler.__init__(self)
        self.serverity_stats = {}
        self.id_stats = {}

    def emit(self, record):
        # Count the number of logs based on severity and id

        if record.levelname not in self.serverity_stats:
            self.serverity_stats[record.levelname] = 0
        self.serverity_stats[record.levelname] += 1

        log_id = record.__dict__.get("log_id", "default_id")
        if log_id == "":
            log_id = "default"
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


class ToffeeFormatter(logging.Formatter):
    """
    Custom formatter for Toffee logs. It supports log_id attribute display in the log record
    """

    def format(self, record):
        if not hasattr(record, "log_id") or record.log_id == "":
            record.log_id = ""
        else:
            record.log_id = f"(id: {record.log_id})"

        log_colors = {
            "DEBUG": BLUE,
            "INFO": WHITE,
            "WARNING": YELLOW,
            "ERROR": RED,
            "CRITICAL": RED,
        }

        color = log_colors.get(record.levelname, WHITE)
        message = super().format(record)
        return f"{color}{message}{RESET}"


#######################################
# Toffee Global Logging Configuration #
#######################################

toffee_logger = logging.getLogger("TOFFEE")


def get_logger() -> logging.Logger:
    """Returns the global logger for Toffee"""

    return toffee_logger


# Global handlers
# stats_handler is used to collect statistics about the logs
stats_handler = StatsHandler()
# screen_handler is used to display logs on the screen
screen_handler = logging.StreamHandler()


# Default format and formatter
default_format = (
    "%(name)s_%(levelname)s @%(filename)s:%(lineno)d%(log_id)s:\t%(message)s"
)
default_formatter = ToffeeFormatter(default_format)

# log levels
INFO = logging.INFO
DEBUG = logging.DEBUG
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL


def setup_logging(
    log_level=WARNING, format=default_format, console_display=True, log_file=None
):
    """
    Setup the logging configuration for Toffee

    Args:
        log_level: The log level for the logger
        format: The format of the log message
        console_display: Whether to display logs on the console
        log_file: The log file name to write logs, if None, logs are not written to a file
    """

    logging.basicConfig(level=log_level, format=format, handlers=[])
    toffee_logger.setLevel(log_level)

    for handler in toffee_logger.handlers[:]:
        toffee_logger.removeHandler(handler)
        handler.close()

    toffee_logger.addHandler(stats_handler)

    if console_display:
        screen_handler.setLevel(log_level)
        screen_handler.setFormatter(default_formatter)
        toffee_logger.addHandler(screen_handler)

    if log_file:
        fh = logging.FileHandler(log_file, mode="w")
        fh.setLevel(log_level)
        fh.setFormatter(default_formatter)
        toffee_logger.addHandler(fh)


setup_logging()

############################
# Toffee Logging Functions #
############################

log = toffee_logger.log
debug = toffee_logger.debug
info = toffee_logger.info
warning = toffee_logger.warning
error = toffee_logger.error
critical = toffee_logger.critical
exception = toffee_logger.exception


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

    toffee_logger.info(summary_str)
