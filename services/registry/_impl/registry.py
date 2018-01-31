import eventlet
eventlet.monkey_patch()

from nameko import rpc
from nameko import containers
import nameko_redis

from ... import base as _base
from ..._utils import (
    config as _config,
    db as _db
)
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
    def add_tags(self, tags):
        tags_in_db = self.get_tags(tags)
        tags = list(set(tags).difference(tags_in_db))
        _query.add_tags(self.session, tags)

    @rpc.rpc
    def get_tags(self, tags=None):
        return [
            (tag.name, tag.popularity)
            for tag in _query.get_tags(self.session, tags)
        ]

    @rpc.rpc
    def add_repos(self, repos):
        tags = []
        for repo_obj in repos:
            for repo, info in repo_obj.items():
                tags.extend(info['tags'])

        # REVIEW: this would be a rpc call, do we want to do this way
        # or a direct query ??
        self.add_tags(list(set(tags)))
        _query.add_repos(self.session, repos)

    # TODO: fix this
    @rpc.rpc
    def get_repos(self, tags=None):
        repos = []
        return _query.get_repos(self.session, tags)
        # for repo_obj in _query.get_repos(self.session, tags):
        #     repos.append({
        #         repo_obj.name: {
        #             'description': repo_obj.description,
        #             'downloads': repo_obj.downloads,
        #             'uri': repo_obj.uri,
        #             'tags': [tag.name for tag in repo_obj.tags]
        #         }
        #     })
        # return repos


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

if __name__ == '__main__':
    service_container = create_container()
    service_container.start()
    service_container.wait()
