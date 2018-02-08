""" Module for base service class.
"""
from nameko import rpc
from ._utils import config as _config


class BaseService(object):
    """ Base service class.
    """
    name = None

    @rpc.rpc
    def ping(self):
        """ Method to test service is reachable.
        """
        return 'pong!'
