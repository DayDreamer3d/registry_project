""" Module for base service class.
"""
from nameko import rpc


class BaseService(object):
    """ Base service class.
    """
    name = None

    @rpc.rpc
    def ping(self):
        """ Method to test service is reachable.
        """
        return 'pong!'
