import os
import yaml


def parse(path):
    with open(path, 'r') as file_h:
        return yaml.load(file_h)


def get_config(service_name):
    """ Protected method to get the service config
        from storage.
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
