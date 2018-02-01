import eventlet
eventlet.monkey_patch()

import operator

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
)
from . import cache as _cache


service_name = 'registry'
config = _config.get_config(service_name)


# TODO: docs please critical for the service
class RegistryService(_base.BaseService):
    name = service_name
    session = _db.DbSession(_models.DeclarativeBase)
    redis = nameko_redis.Redis(config['WORKING_ENV'])

    @rpc.rpc
    def add_tags(self, tags):
        tags_in_db = self.get_tags(tags)

        tags_to_add = list(
            set(tags).difference([tag.name for tag in tags_in_db])
        )
        _query.add_tags(self.session, tags_to_add)

        # _cache.add_tags([(tag, 1) for tag in tags])

    @rpc.rpc
    def get_tags(self, tags=None):
        result = _cache.get_tags(self.redis, config['CACHE']['KEY'], tags)

        remaining_tags = [name for name, popularity in result if name not in tags]

        if remaining_tags:
            db_result = [
                tuple(tag.name, tag.popularity)
                for tag in _query.get_tags(self.session, tags)
            ]

            # update the cache
            # _cache.add_tags(db_result)

            result = list(set(result).union(db_result))
            result.sort(key=operator.itemgetter(1), reverse=True)

        return result

    @rpc.rpc
    def add_repos(self, repos):
        # get the tags associated with given repos
        tags = []
        for repo_obj in repos:
            for repo, info in repo_obj.items():
                tags.extend(info['tags'])

        # Only update the unique tags
        # REVIEW: this would be a rpc call, do we want to do this way
        # or a direct query ??
        self.add_tags(list(set(tags)))

        # update popularity for tags (include duplicates)
        _query.update_popularity(tags)
        added_repos = _query.add_repos(self.session, repos)

        # if tag in cache
        if added_repos:
            _cache.add_repos(added_repos)
        # update tag key and repo

    # TODO: fix this service method to get the items from db
    @rpc.rpc
    def get_repos(self, tags=None):
        # _query.update_popularity(tags)

        # fetch from cache
        cached_repos, non_cached_tags = _cache.get_repos(tags)

        # fetch only non cached tag tags from db
        db_repos = []
        if non_cached_tags:
            db_repos = _query.get_repos(self.session, non_cached_tags)

        # update cache with non cached tag results
        if db_repos:
            _cache.add_repos(db_repos)

        return repos

    @rpc.rpc
    @_cache.update_repo_downloads([repo])
    def update_repo_downloads(self, repo):
        _query.update_downloads([repo])


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
