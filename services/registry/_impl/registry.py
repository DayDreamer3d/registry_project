import eventlet
eventlet.monkey_patch()

import operator

from nameko import containers, rpc
import nameko_redis
import nameko_logstash

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
    redis = nameko_redis.Redis('services')
    log = nameko_logstash.LogstashDependency(
        local_file=os.path.join(
            config['LOGGING']['DIR'],
            '{}.yml'.format(service_name)
        )
    )

    @rpc.rpc
    def add_tags(self, tags):
        tags_in_db = self.get_tags(tags)

        tags_to_add = list(
            set(tags).difference([tag[0] for tag in tags_in_db])
        )
        _query.add_tags(self.session, tags_to_add)

        tags = [(tag, 1) for tag in tags]
        _cache.add_tags(self.redis, config['CACHE']['KEY'], tags)

    @rpc.rpc
    def get_tags(self, tags=None):
        tags = tags or []
        cached_tags, non_cached_tags = [], []

        try:
            cached_tags, non_cached_tags = _cache.get_tags(
                self.redis,
                config['CACHE']['KEY'],
                tags
            )
        except Exception as e:
            # TODO: log Exception
            pass

        if cached_tags and not non_cached_tags:
            return cached_tags + non_cached_tags

        non_cached_tags = [
            (tag.name, tag.popularity)
            for tag in _query.get_tags(self.session, non_cached_tags)
        ]

        _cache.add_tags(self.redis, config['CACHE']['KEY'], non_cached_tags)

        return cached_tags + non_cached_tags

    @rpc.rpc
    def add_repos(self, repos):
        # get the tags associated with given repos
        tags = []
        for repo_obj in repos:
            for repo, info in repo_obj.items():
                tags.extend(info['tags'])

        # Only update the unique and new tags
        # REVIEW: this would be a rpc call, do we want to do this way
        # or a direct query ??
        self.add_tags(list(set(tags)))

        # update popularity for tags (include duplicates)
        # _query.update_popularity(self.session, tags)

        added_repos = _query.add_repos(self.session, repos)

        if added_repos:
            try:
                _cache.add_repos(
                    self.redis,
                    config['CACHE']['KEY'],
                    added_repos,
                    only_update=True
                )
            except Exception:
                # TODO: log exception
                pass

    @rpc.rpc
    def get_repos(self, tags=None):
        # Check the labels
        # for existent tags (cached tags) -> get the repos
        # for non cached tags -> get it from db
        # update the labels in cache
        # update missing repos
        # TODO: for now get all the repos from db
        tags = tags or []

        # fetch from cache
        cached_repos, non_cached_tags = _cache.get_repos_from_tags(
            self.redis,
            config['CACHE']['KEY'],
            tags
        )

        # fetch only non cached tags from db
        db_repos = _query.get_repos_from_tags(self.session, non_cached_tags)

        # update cache with non cached tag results
        if db_repos:
            _cache.add_repos(self.redis, config['CACHE']['KEY'], db_repos)

        _query.update_popularity(self.session, tags)

        db_repos = [
            {
                'name': repo.name,
                'description': repo.description,
                'downloads': repo.downloads,
                'uri': repo.uri,
                'tags': [tag.name for tag in repo.labels]
            }
            for repo in db_repos
        ]
        repos = cached_repos + db_repos
        self.update_downloads([repo['name'] for repo in repos])

        return repos

    @rpc.rpc
    def get_repo(self, repo):
        result = {}

        try:
            result = _cache.get_repo_details(self.redis, config['CACHE']['KEY'], repo)
        except Exception as e:
            # TODO: log Exception
            pass

        if result:
            return result

        repo = _query.get_repo_details(self.session, repo)

        # cache the result
        _cache.add_repos(self.redis, config['CACHE']['KEY'], [repo])

        return {
            'name': repo.name,
            'tags': [tag.name for tag in repo.labels],
            'description': repo.description,
            'downloads': repo.downloads,
            'uri': repo.uri,
        }

    @rpc.rpc
    def update_downloads(self, repos):
        # _cache.update_downloads([repo])
        _query.update_downloads(self.session, repos)


def create_container():
    service_container = containers.ServiceContainer(
        RegistryService,
        config=config
    )
    return service_container


if __name__ == '__main__':
    service_container = create_container()
    service_container.start()
    service_container.wait()
