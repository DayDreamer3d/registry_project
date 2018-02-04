import logging

# TODO: add this into config
cache_key_delimiter = ':'

# REVIEW: what about having cache as a service

# TODO: check O notation for redis commands
# TODO: these cache functions could be in class.


service_name = 'registry'
logger = logging.getLogger('services_{}'.format(service_name))


def add_tags(redis, cache_key, tags):
    key = cache_key_delimiter.join([cache_key, 'tags'])

    items = []
    for tag in tags:
        items.append(int(tag[1]))  # popularity as score
        items.append(tag[0])  # tag name

    with redis.pipeline() as pipe:
        pipe.zadd(key, *items).execute()

        logger.debug('{} tags are added to cache.'.format(tags))


def get_tags(redis, cache_key, tags):
    key = cache_key_delimiter.join([cache_key, 'tags'])

    logger.debug('Get details for Tag({}) from cache.'.format(tags))

    with redis.pipeline() as pipe:
        if tags:
            cached_tags, non_cached_tags = [], []

            for tag in tags:
                popularity = pipe.zscore(key, tag).execute()[0]
                if popularity:
                    cached_tags.append((tag, popularity))
                else:
                    non_cached_tags.append(tag)

            logger.debug('Cached tags: {}\nNon cached tags: {}.'.format(cached_tags, non_cached_tags))

            return cached_tags, non_cached_tags

        else:
            cached_tags = pipe.zrevrangebyscore(key, '+inf', 0, withscores=True).execute()
            cached_tags = [
                (tag, int(popularity))
                for tag, popularity in cached_tags[0]
            ]

            logger.debug('Cached tags: {}\nNon cached tags: {}.'.format(cached_tags, []))

            return cached_tags, []


def add_repos(redis, cache_key, repos, only_update=False):
    logger.debug('Repos to be added to cache are: {}.'.format(repos))

    label_key = cache_key_delimiter.join([cache_key, 'labels'])
    repo_key = cache_key_delimiter.join([cache_key, 'repos'])
    tag_key = cache_key_delimiter.join([cache_key, 'tags'])

    # search how many tags are in cache
    with redis.pipeline() as pipe:
        for repo in repos:

            if not repo.labels:
                logger.warn('{} Repo can not be added to cache. No tags are found.'.format(repo))
                continue

            for tag in repo.labels:
                # update popularity for tag (not labels)
                pipe.zincrby(tag_key, tag.name).execute()

                # intenionally using redis than pipeline
                # because pipeline will buffer the below commands
                # and will execute the first buffered command here
                # which would give the undesired result
                # TODO: look deep in pipelining and find solution

                # only add repo if that tag is present in the cache
                # it's an update strategy to keep the cache fresh for a particular tag
                if only_update and redis.zscore(label_key, tag.name) is None:
                    logger.debug('For Repo({}), Tag({}) not found in Label({}) in cache.'.format(repo.name, tag.name, label_key))
                    continue

                # update mapping between tag and repo
                label_item_key = cache_key_delimiter.join([label_key, tag.name])
                pipe.zadd(label_item_key, repo.downloads, repo.name).execute()

                logger.debug('For Repo({}) added to the cache under Label({}) key.'.format(repo.name, tag.name, label_item_key))

            key = cache_key_delimiter.join([repo_key, repo.name])
            pipe.hmset(
                key, {
                    'description': repo.description,
                    'uri': repo.uri,
                    'tags': [tag.name for tag in repo.labels]
                }
            ).execute()

            logger.debug('For Repo({}) hash added to cache.'.format(repo.name))


def get_repos_from_tags(redis, cache_key, tags=None):
    tags = tags or [name for name, download in get_tags(redis, cache_key, tags)[0]]

    logger.debug('Tags({}) would be used to retrieve associated repos.'.format(tags,))

    label_key = cache_key_delimiter.join([cache_key, 'labels'])
    repo_key = cache_key_delimiter.join([cache_key, 'repos'])

    non_cached_tags = []
    result = []

    with redis.pipeline() as pipe:
        # get repos per tag basis
        repos = []
        for tag in tags:
            label_item_key = cache_key_delimiter.join([label_key, tag])

            repos_per_tag = []
            if pipe.exists(label_item_key).execute()[0]:
                repos_per_tag = pipe.zrevrangebyscore(
                    label_item_key, '+inf', 0, withscores=True).execute()[0]

                repo_names = [repo.name for repo in repos]
                logger.debug('Repos({}) for Tag({}).'.format(repo_names, tag))

            # if tag doesn't exists in cache
            # skip it and eventually get its result from db
            if repos_per_tag:
                for r in repos_per_tag:
                    if r not in repos:
                        repos.append(r)
            else:
                non_cached_tags.append(tag)

        for repo, downloads in repos:
            repo_item_key = cache_key_delimiter.join([repo_key, repo])

            if not pipe.exists(repo_item_key).execute()[0]:
                continue

            repo_item = pipe.hgetall(repo_item_key).execute()[0]
            repo_item.update({
                'name': repo,
                'downloads': int(downloads)
            })
            result.append(repo_item)

            logger.debug('Repos({}) added in cache.'.format(repo_item_key))

        pipe.execute()

    return result, non_cached_tags


def get_repo_details(redis, cache_key, repo):
    key = cache_key_delimiter.join([cache_key, 'repos', repo])
    details = redis.hgetall(key)
    logger.debug('Repo({}) details are : {}.'.format(repo, details))
    return details
