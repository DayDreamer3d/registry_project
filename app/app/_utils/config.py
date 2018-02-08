""" Module to get the config for the app.
"""

import os
import yaml


def get_config():
    """ Function to get the app config
        from storage.

        Returns:
            dict: containing contents of the file.
    """
    path = os.path.join(
        os.path.dirname(__loader__.path),
        '..',
        'config.yml'
    )
    with open(path, 'r') as file_h:
        return yaml.load(file_h)
