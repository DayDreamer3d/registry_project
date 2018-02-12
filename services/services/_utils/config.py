""" Utility module related to config parsing.
"""
import collections
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
    service_config = parse(get_config_path(service_name))
    for category, details in service_config.items():
        if category in config:
            if isinstance(config.get(category), collections.MutableMapping):
                config[category].update(details)
        else:
            config[category] = details

    return config
