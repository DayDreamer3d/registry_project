""" Utility module related to config parsing.
"""

import os
import yaml


def parse(path):
    """ Parse the given yaml file.

        Args:
            path(str): path to the yaml file.

        Returns:
            dict: containing contents of the file.
    """
    with open(path, 'r') as file_h:
        return yaml.load(file_h)


def get_config(service_name):
    """ Function to get the service config
        from storage.

        Args:
            service_name (str): service name

        Returns:
            dict: final config entries for the service.
    """
    def get_config_path(mid_dir=''):
        path = os.path.join(
            os.path.dirname(__loader__.path),
            '..',
            mid_dir,
            'config.yml'
        )
        return os.path.abspath(path)

    # parse base config
    config = parse(get_config_path())

    # override/add  service config
    config.update(parse(get_config_path(service_name)))

    return config
