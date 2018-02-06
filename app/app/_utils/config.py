import os
import yaml


def get_config():
    """ Protected method to get the service config
        from storage.
    """
    path = os.path.join(
        os.path.dirname(__loader__.path),
        '..',
        'config.yml'
    )
    with open(path, 'r') as file_h:
        return yaml.load(file_h)
