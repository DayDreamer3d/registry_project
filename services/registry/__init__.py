from _utils import config, log

service_name = 'registry'

config = config.get_config(service_name)

logger = log.create_file_logger(
    service_name,
    config['LOGGING']['LEVEL'],
    log.create_log_file(config['LOGGING']['DIR'], service_name),
)
