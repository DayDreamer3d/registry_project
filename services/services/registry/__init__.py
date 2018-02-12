from .._utils import (
    config as _config,
    log as _log
)

service_name = 'registry'

config = _config.get_config(service_name)

logger = _log.create_file_logger(
    service_name,
    config['LOGGING']['LEVEL'],
    _log.create_log_file(config['LOGGING']['DIR'], service_name),
)
