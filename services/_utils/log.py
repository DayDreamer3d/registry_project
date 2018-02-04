import os
import logging
import logstash_formatter


def create_log_file(dir_, service_name):
    log_file = os.path.join(dir_, '{}.log'.format(service_name))
    if not os.path.exists(dir_):
        os.makedirs(dir_)
        open(log_file, 'a').close()
    return log_file


def create_file_logger(service_name, log_level, log_file):
    logger = logging.getLogger('services_{}'.format(service_name))
    handler = logging.FileHandler(log_file)
    formatter = logstash_formatter.LogstashFormatterV1()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(log_level)
    return logger
