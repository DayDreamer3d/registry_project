""" Registry service module containing all the public entrypoints for the service.

"""
# monkey paching should be at top level.
import eventlet
eventlet.monkey_patch()

import operator

from nameko import containers, rpc
import nameko_redis

from ... import base as _base
from ..._utils import (
    config as _config,
    db as _db,
    log as _log
)
from . import (
    cache as _cache,
    models as _models,
    query as _query,
)


service_name = 'registry'
config = _config.get_config(service_name)
logger = _log.create_file_logger(
    service_name,
    config['LOGGING']['LEVEL'],
    _log.create_log_file(config['LOGGING']['DIR'], service_name),
)


# TODO: docs please critical for the service
class RegistryService(_base.BaseService):
    name = service_name
    session = _db.DbSession(_models.DeclarativeBase)
    redis = nameko_redis.Redis('services')

    @rpc.rpc
    def get_tags(self, tags=None):
        tags = tags or []
        logger.debug('Tags supplied are : {}'.format(tags))
        cached_tags, non_cached_tags = [], []

        try:
            cached_tags, non_cached_tags = _cache.get_tags(
                self.redis,
                config['CACHE']['KEY'],
                tags
            )
        except Exception as e:
            logger.error(
                'Exception occurred while fetching cache.',
                exc_info=True
            )

        if cached_tags and not non_cached_tags:
            logger.info(
                'Result: Fetched Tags({}). Unfectched Tags({}).'.format(cached_tags, non_cached_tags),
            )
            return cached_tags + non_cached_tags

        non_cached_tags = [
            (tag.name, tag.popularity)
            for tag in _query.get_tags(self.session, non_cached_tags)
        ]

        logger.info(
            'Tags({}) fetched from db.'.format(non_cached_tags)
        )

        if non_cached_tags:
            _cache.add_tags(self.redis, config['CACHE']['KEY'], non_cached_tags)

            logger.info(
                'Tags({}) added to the cache.'.format(non_cached_tags),
            )

        logger.info(
            'Result: Fetched Tags({}). Unfectched Tags({}).'.format(cached_tags, non_cached_tags),
        )

        return cached_tags + non_cached_tags

    @rpc.rpc
    def add_tags(self, tags):
        tags_in_db = self.get_tags(tags)

        tags_to_add = list(
            set(tags).difference([tag[0] for tag in tags_in_db])
        )
        _query.add_tags(self.session, tags_to_add)

        logger.info(
            'Tags({}) added to db.'.format(tags_to_add),
        )

        tag_objs = [(tag, 1) for tag in tags]
        _cache.add_tags(self.redis, config['CACHE']['KEY'], tag_objs)

        logger.info(
            'Tags({}) added to cache.'.format(tags),
        )

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

        repo_names = [repo.name for repo in added_repos]
        logger.info(
            'Repos({}) added to db.'.format(repo_names),
        )

        if added_repos:
            try:
                _cache.update_repos(self.redis, config['CACHE']['KEY'], added_repos)

                repo_names = [repo.name for repo in added_repos]
                logger.info(
                    'Repos({}) added to cache.'.format(repo_names),
                )
            except Exception:
                logger.error(
                    'Exception occurred while updating Repos() to cache.'.format(repo_names),
                    exc_info=True
                )

    @rpc.rpc
    def get_repos(self, tags=None):
        tags = tags or []

        if tags:
            _query.update_popularity(self.session, tags)

        # fetch from cache
        cached_repos, non_cached_tags = _cache.get_repos_from_tags(
            self.redis,
            config['CACHE']['KEY'],
            tags,
        )

        for c_repo in cached_repos:
            c_repo['tags'] = eval(c_repo['tags'])

        logger.info(
            'Repos({}) fetched from cache.\n Tags({}) are not in cache'.format(cached_repos, non_cached_tags)
        )

        # fetch only non cached tags from db
        db_repos = []
        if non_cached_tags:
            db_repos = _query.get_repos_from_tags(self.session, non_cached_tags)

        db_repo_names = [repo.name for repo in db_repos]
        logger.info(
            'Repos({}) fetched from db.'.format(db_repo_names)
        )

        if db_repos:
            # only add repos which belong to queried tags.
            # tags = cached + non cached tags as there could be repos
            # which belongs to cached tags and are not yet in cache.
            try:
                _cache.add_repos(self.redis, config['CACHE']['KEY'], tags, db_repos)
                logger.info(
                    'Repos({}) added to cache.'.format(db_repo_names)
                )
            except Exception:
                logger.error(
                    'Exception occurred while adding Repos({}) to cache.'.format(db_repo_names),
                    exc_info=True
                )

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

        repos = cached_repos
        cached_names = [c_name['name'] for c_name in cached_repos]
        for repo in db_repos:
            if repo['name'] not in cached_names:
                repos.append(repo)

        repo_names = [repo['name'] for repo in repos]

        if repo_names:
            self.update_downloads(repo_names)

        logger.info(
            'Result: Repos({}).'.format(repo_names)
        )

        return repos

    @rpc.rpc
    def get_repo(self, repo):
        result = {}

        try:
            result = _cache.get_repo_details(self.redis, config['CACHE']['KEY'], repo) or {}
        except Exception as e:
            logger.error(
                'Exception occurred while fetching cache.',
                exc_info=True
            )

        if result:
            logger.info('Repo({}) details fetched from cache.'.format(result))
            result['tags'] = eval(result['tags'])
            return result

        repo_details = _query.get_repo_details(self.session, repo)

        if not repo_details:
            return repo_details

        _cache.add_repos(self.redis, config['CACHE']['KEY'], [repo_details])
        logger.info('Repo({}) added to cache.'.format(repo))

        return {
            'name': repo_details.name,
            'tags': [tag.name for tag in repo_details.labels],
            'description': repo_details.description,
            'downloads': repo_details.downloads,
            'uri': repo_details.uri,
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
