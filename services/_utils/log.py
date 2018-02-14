""" Utility module for logging.
"""

import os
import logging
import logstash_formatter


def create_log_file(dir_, service_name):
    """ Create the log file on storage.

        Args:
            dir_ (str): Parent director for the logs.
            service_name (str): service name for which logs will be generated.

        Returns:
            str: full path of the log file.
    """
    log_file = os.path.join(dir_, '{}.log'.format(service_name))
    if not os.path.exists(dir_):
        os.makedirs(dir_)
        open(log_file, 'a').close()
    return log_file


def create_file_logger(service_name, log_level, log_file):
    """ Create the named logger for the service.

        Args:
            service_name(str): service name for which logger would be created.
            log_level(str): logging severity.
            log_file(str): full path of the log file.

        Returns:
            logger object: logger object for the service.
    """
    logger = logging.getLogger('services_{}'.format(service_name))
    handler = logging.FileHandler(log_file)
    formatter = logstash_formatter.LogstashFormatterV1()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(log_level)
    return logger
