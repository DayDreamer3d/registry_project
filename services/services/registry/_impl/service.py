""" Registry service module containing all the public entrypoints for the service.
"""
# monkey paching should be first before nameko import.

import eventlet
eventlet.monkey_patch()

import operator

from nameko import containers, rpc

from ... import base as _base
from ..._utils import (
    config as _config,
    log as _log
)
from . import (
    cache as _cache,
    models as _models,
    db as _db,
)


service_name = 'registry'
config = _config.get_config(service_name)
logger = _log.create_file_logger(
    service_name,
    config['LOGGING']['LEVEL'],
    _log.create_log_file(config['LOGGING']['DIR'], service_name),
)


def _repo_info(repo):
    return {
        'name': repo.name,
        'description': repo.description,
        'downloads': repo.downloads,
        'uri': repo.uri,
        'tags': [tag.name for tag in repo.labels]
    }


# TODO: docs please critical for the service
class RegistryService(_base.BaseService):
    name = service_name
    db = _db.RegistryDatabaseSession(_models.DeclarativeBase)
    cache = _cache.RegistryCache()

    @rpc.rpc
    def get_tags(self, tags=None):
        tags = tags or []
        logger.debug('Tags supplied are : {}'.format(tags))
        cached_tags, non_cached_tags = [], []

        try:
            cached_tags, non_cached_tags = self.cache.get_tags(tags)
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
            for tag in self.db.get_tags(non_cached_tags)
        ]

        logger.info(
            'Tags({}) fetched from db.'.format(non_cached_tags)
        )

        if non_cached_tags:
            self.cache.add_tags(non_cached_tags)

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
        self.db.add_tags(tags_to_add)

        logger.info('Tags({}) added to db.'.format(tags_to_add))

        tag_objs = [(tag, 1) for tag in tags]
        self.cache.add_tags(tag_objs)

        logger.info('Tags({}) added to cache.'.format(tags))

    @rpc.rpc
    def add_repos(self, repos):
        # get the tags associated with given repos
        tags = []
        for repo_obj in repos:
            tags.extend(repo_obj['tags'])

        # Only update the unique and new tags
        # REVIEW: this would be a rpc call, do we want to do this way
        # or a direct query ??
        self.add_tags(list(set(tags)))

        added_repos = self.db.add_repos(repos)

        repo_names = [repo.name for repo in added_repos]
        logger.info('Repos({}) added to db.'.format(repo_names))

        if added_repos:
            try:
                self.cache.update_repos(added_repos)

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
            self.db.update_popularity(tags)

        # fetch from cache
        cached_repos, non_cached_tags = self.cache.get_repos_from_tags(tags)

        for c_repo in cached_repos:
            c_repo['tags'] = eval(c_repo['tags'])

        logger.info(
            'Repos({}) fetched from cache.\n Tags({}) are not in cache'.format(cached_repos, non_cached_tags)
        )

        # fetch only non cached tags from db
        db_repos = []
        if not cached_repos or non_cached_tags:
            db_repos = self.db.get_repos_from_tags(non_cached_tags)

        db_repo_names = [repo.name for repo in db_repos]
        logger.info(
            'Repos({}) fetched from db.'.format(db_repo_names)
        )

        if db_repos:
            # only add repos which belong to queried tags.
            # tags = cached + non cached tags as there could be repos
            # which belong to cached tags and are not yet in cache.
            try:
                self.cache.add_repos(tags, db_repos)
                logger.info(
                    'Repos({}) added to cache.'.format(db_repo_names)
                )
            except Exception:
                logger.error(
                    'Exception occurred while adding Repos({}) to cache.'.format(db_repo_names),
                    exc_info=True
                )

        db_repos = [
            _repo_info(repo)
            for repo in db_repos
        ]

        #  get unique repos for final result
        repos = cached_repos + db_repos
        repos = list({repo['name']: repo for repo in repos}.values())
        repo_names = [repo['name'] for repo in repos]

        logger.info(
            'Result: Repos({}).'.format(repo_names)
        )

        return repos

    @rpc.rpc
    def get_repo(self, repo):
        result = {}

        try:
            result = self.cache.get_repo_details(repo) or {}
        except Exception as e:
            logger.error(
                'Exception occurred while fetching cache.',
                exc_info=True
            )

        if result:
            logger.info('Repo({}) details fetched from cache.'.format(repo))
            result['tags'] = eval(result['tags'])
            return result

        repo_details = self.db.get_repo_details(repo)

        if not repo_details:
            return repo_details

        self.cache.update_repos([repo_details])
        logger.info('Repo({}) added to cache.'.format(repo))

        # TODO: there are other places where same dict of repo details are getting used.
        # should be a skeleton dict and reference it here to fill the values.
        return _repo_info(repo_details)

    @rpc.rpc
    def update_downloads(self, repo):
        try:
            self.cache.update_downloads([repo])
        except Exception as e:
            logger.error(
                'Exception occurred while updating downloads for Repo({}).'.format(repo),
                exc_info=True
            )
        self.db.update_downloads([repo])


def create_container():
    return containers.ServiceContainer(RegistryService, config=config)


if __name__ == '__main__':
    service_container = create_container()
    service_container.start()
    service_container.wait()
