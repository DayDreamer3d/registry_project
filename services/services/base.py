""" Base service class.
"""
from nameko import rpc
from ._utils import config as _config


class BaseService(object):
    name = None

    @rpc.rpc
    def ping(self):
        """ Method to test service is reachable.
        """
        return 'pong!'
