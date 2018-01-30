import eventlet
eventlet.monkey_patch()

from nameko import rpc
from nameko import containers
import nameko_redis

from ... import base as _base
from ..._utils import config as _config
from .orm import (
    models as _models,
    query as _query,
    session as _session
)


service_name = 'registry'

# TODO: docs please critical for the service
class RegistryService(_base.BaseService):
    name = service_name
    config = _config.get_config(service_name)
    session = _session.DbSession(_models.DeclarativeBase)

    def __init__(self, config=None):

        # redis cache related
        self.repo_key = self.config['CACHE']['KEY']
        self.redis = nameko_redis.Redis(self.config['WORKING_ENV'])

        # logging
        # self.log = _log.Logging()

    @rpc.rpc
    def get_tags(self):
        return _query.get_tags(self.session)

    @rpc.rpc
    def add_repos(self, repos):
        return _query.add_repos(self.session, repos)

    @rpc.rpc
    def get_repos_from_tags(self, tags):
        return _query.get_repos(self.session, tags)


def create_container():
    service_container = containers.ServiceContainer(
        RegistryService,
        config=RegistryService.config
    )
    return service_container

# service_container.start()
# service_container.wait()


    # @rpc.rpc
    # def get_tags(self):
    #     """ Get the tags for repositories
    #     """
    #
    #     # try to get the people from cache.
    #     try:
    #         people = _cache.get_people(self.redis, self.repo_key)
    #         _log.get_people(self.log, 'info', self.repo_key, people, 'cache')
    #         return people
    #
    #     except Exception as e:
    #         _log.log(self.log, 'warn', str(e).encode())
    #
    #         # try from db
    #         try:
    #             people = _orm.get_all_people(self.session, _models.Person)
    #             _log.get_people(self.log, 'info', self.repo_key, people, 'db')
    #
    #             # cache missing these entries, add them to cache
    #             try:
    #                 _cache.add_people(self.redis, self.repo_key, people)
    #             except Exception as e:
    #                 _log.log(self.log, 'warn', str(e).encode())
    #
    #             # get values from cache
    #             return _cache.get_people(self.redis, self.repo_key)
    #
    #         except Exception as e:
    #             _log.log(self.log, 'error', str(e).encode())
    #
    # @rpc.rpc
    # def get_repos(self, tags=()):
    #     pass
