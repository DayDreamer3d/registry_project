""" Caching operations for the service.
"""

import logging
import nameko_redis

import registry


# REVIEW: what about having cache as a service


class RegistryCache(nameko_redis.Redis):
    """ Sub-class of redis nameko extension.
    """
    def __init__(self):
        super().__init__(registry.config['CACHE']['LAYER'])

    def get_dependency(self, worker_ctx):
        return RegistryCacheWrapper(self.client)


class RegistryCacheWrapper(object):
    """ Registry cache wrapper class which defines all the cache operations.
    """

    def __init__(self, client):
        self.cache_key = registry.config['CACHE']['KEY']
        self.delimiter = registry.config['CACHE']['DELIMITER']
        self.client = client

        self.tags_key = self.delimiter.join([self.cache_key, 'tags'])
        self.labels_key = self.delimiter.join([self.cache_key, 'labels'])
        self.repos_key = self.delimiter.join([self.cache_key, 'repos'])

    def add_tags(self, tags):
        """ Add the tags to the cache.

            Args:
                tags (list): list of tags that would be inserted in cache.
        """
        items = []
        for tag in tags:
            items.append(int(tag[1]))  # popularity as score
            items.append(tag[0])  # tag name

        with self.client.pipeline() as pipe:
            pipe.zadd(self.tags_key, *items).execute()
            registry.logger.debug('Tags({}) tags are added to cache.'.format(tags))

    def get_tags(self, tags):
        """ Get the tags from the cache.

            Args:
                tags (list): list of tags that would be fetched from cache.

            Retuns:
                tuple: pair of tags cached tags and non cached tags.
        """
        key = self.delimiter.join([self.cache_key, 'tags'])

        registry.logger.debug('Get details for Tag({}) from cache.'.format(tags))
        with self.client.pipeline() as pipe:
            if tags:
                cached_tags, non_cached_tags = [], []

                for tag in tags:
                    pipe.zscore(key, tag)

                popularity = pipe.execute()

                for tag, popularity in zip(tags, popularity):
                    if popularity:
                        cached_tags.append((tag, popularity))
                    else:
                        non_cached_tags.append(tag)

                registry.logger.debug('Cached tags: {}\nNon cached tags: {}.'.format(cached_tags, non_cached_tags))

                return cached_tags, non_cached_tags

            else:
                cached_tags = pipe.zrevrangebyscore(key, '+inf', 0, withscores=True).execute()
                cached_tags = [
                    (tag, int(popularity))
                    for tag, popularity in cached_tags[0]
                ]

                registry.logger.debug('Cached tags: {}\nNon cached tags: {}.'.format(cached_tags, []))

                return cached_tags, []

    def update_repos(self, repos):
        """ Update the repositories entries in cache
            if any of its corresponding tags exist in cache.

            Args:
                repos (list): list of repositories that would be updated in cache.
        """
        repo_names = [repo for repo in repos]

        with self.client.pipeline() as pipe:
            repos_to_add = []
            labels_to_add = []

            for repo in repos:

                label_names = []

                for tag in repo.labels:
                    pipe.zadd(self.tags_key, 0, tag.name)
                    label_names.append(tag.name)

                pipe.execute()

                for label in label_names:
                    # add the repo iff this tag exists in labels.
                    label_item_key = self.delimiter.join([self.labels_key, label])
                    if not pipe.exists(label_item_key).execute()[0]:
                        continue

                    labels_to_add.append([label_item_key, repo.downloads, repo.name])

                    repo_item_key = self.delimiter.join([self.repos_key, repo.name])
                    if pipe.exists(repo_item_key).execute()[0]:
                        continue

                    repos_to_add.append({
                        'name': repo.name,
                        'description': repo.description,
                        'uri': repo.uri,
                        'tags': label_names,
                        'downloads': repo.downloads
                    })

            for repo in repos_to_add:
                key = self.delimiter.join([self.repos_key, repo['name']])
                pipe.hmset(key, repo)

            for label in labels_to_add:
                pipe.zadd(*label)

            pipe.execute()

        registry.logger.debug('Labels({}) are added to cache.'.format([label[0] for label in labels_to_add]))
        registry.logger.debug('Repos({}) added to cache.'.format(repo_names))

    def add_repos(self, tags, repos):
        """ Add the repositories entries in cache.

            Args:
                tags (list): list of tags that are supplied by client, only add repositores for these tags.
                repos (list): list of repositories that would be added in cache.
        """
        tags = tags or []
        repos = repos or []

        with self.client.pipeline() as pipe:
            # increment the popularity of tags
            for tag in tags:
                pipe.zincrby(self.tags_key, tag)

            for repo in repos:
                labels = [label.name for label in repo.labels]
                to_update_tags = set(labels).intersection(tags)

                for tag in to_update_tags:
                    label_item_key = self.delimiter.join([self.labels_key, tag])
                    pipe.zadd(label_item_key, repo.downloads, repo.name)

                key = self.delimiter.join([self.repos_key, repo.name])
                pipe.hmset(key, {
                    'name': repo.name,
                    'description': repo.description,
                    'uri': repo.uri,
                    'tags': labels,
                })

            pipe.execute()

    def get_repos_from_tags(self, tags=None):
        """ Get the repositories from the cache based on given tags.

            Args:
                tags (list): list of tags for which the repositories will be fetched from cache.

            Retuns:
                tuple: pair of tags cached tags and non cached tags.
        """
        tags = tags or [name for name, download in self.get_tags(tags)[0]]

        registry.logger.debug('Get the repos for Tags({}) from cache.'.format(tags))

        non_cached_tags = []
        result = []

        with self.client.pipeline() as pipe:
            # get repos per tag basis
            repos = []
            for tag in tags:

                label_item_key = self.delimiter.join([self.labels_key, tag])

                repos_per_tag = []
                if pipe.exists(label_item_key).execute()[0]:
                    repos_per_tag = pipe.zrevrangebyscore(
                        label_item_key, '+inf', 0, withscores=True).execute()[0]

                    repo_names = [repo[0] for repo in repos_per_tag]
                    registry.logger.debug('Repos({}) under Label({}).'.format(repo_names, label_item_key))

                # if tag doesn't exists in cache
                # skip it and eventually get its result from db
                if repos_per_tag:
                    for r in repos_per_tag:
                        if r not in repos:
                            repos.append(r)
                else:
                    non_cached_tags.append(tag)

            for repo, downloads in repos:
                repo_item_key = self.delimiter.join([self.repos_key, repo])

                if not pipe.exists(repo_item_key).execute()[0]:
                    continue

                repo_item = pipe.hgetall(repo_item_key).execute()[0]
                repo_item.update({
                    'name': repo,
                    'downloads': int(downloads)
                })
                result.append(repo_item)

            pipe.execute()

        registry.logger.debug('Repos({}) added in cache. Non Cahed Tags({})'.format(result, non_cached_tags))

        return result, non_cached_tags

    def get_repo_details(self, repo):
        """ Get the repository details from the cache.

            Args:
                repo (str): name of the repository for which details will be presented.

            Retuns:
                dict: of details for the repository.
        """
        key = self.delimiter.join([self.repos_key, repo])

        with self.client.pipeline() as pipe:
            details = pipe.hgetall(key).execute()[0]

            if not details:
                return {}

            details['tags'] = eval(details['tags'])
            for label in details['tags']:
                label_item_key = self.delimiter.join([self.labels_key, label])
                if not pipe.exists(label_item_key).execute()[0]:
                    continue

                downloads = pipe.zscore(label_item_key, repo).execute[0]
                dsetails['downloads'] = int(downloads)

                # checking single label is enough because
                # for any tag, repository details would be the same
                break

        if details:
            registry.logger.debug('Repo({}) Details({}) are fetched from cache.'.format(repo, details))

        return details

    def update_downloads(self, repos):
        """ Update the repositories downloads attribute in cache

            Args:
                repos (list): list of repository names.
        """
        with self.client.pipeline() as pipe:
            repos_to_update = []
            labels_to_update = []

            for repo in repos:
                # collect all the repos need to be updated
                repo_item_key = self.delimiter.join([self.repos_key, repo])
                if not pipe.exists(repo_item_key).execute()[0]:
                    continue
                repos_to_update.append(repo_item_key)

                # collect all the labels need to be updated
                labels = eval(pipe.hget(repo_item_key, 'tags').execute()[0])
                for label in labels:
                    label_item_key = self.delimiter.join([self.labels_key, label])
                    if not pipe.exists(label_item_key).execute()[0]:
                        continue
                    labels_to_update.append((label_item_key, repo))

            # update  repos and labels
            for repo_item in repos_to_update:
                pipe.hincrby(repo_item, 'downloads', 1)

            for label_item, repo in labels_to_update:
                pipe.zincrby(label_item, repo, 1)

            pipe.execute()
