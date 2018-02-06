import logging

# TODO: add this into config
cache_key_delimiter = ':'

# REVIEW: what about having cache as a service

# TODO: these cache functions could be in class.
# TODO: refactor the code for this module, IMP: try better pipeling for redsis.

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


def update_repos(redis, cache_key, repos):
    repo_names = [repo for repo in repos]

    label_key = cache_key_delimiter.join([cache_key, 'labels'])
    repo_key = cache_key_delimiter.join([cache_key, 'repos'])
    tag_key = cache_key_delimiter.join([cache_key, 'tags'])

    with redis.pipeline() as pipe:
        repos_to_add = []
        labels_to_add = []

        for repo in repos:

            label_names = []

            for tag in repo.labels:
                pipe.zadd(tag_key, 0, tag.name)
                label_names.append(tag.name)

            pipe.execute()

            for label in label_names:
                # add the repo iff this tag exists in labels.
                label_item_key = cache_key_delimiter.join([label_key, label])
                if not pipe.exists(label_item_key).execute()[0]:
                    continue

                labels_to_add.append([label_item_key, repo.downloads, repo.name])

                repo_item_key = cache_key_delimiter.join([repo_key, repo.name])
                if pipe.exists(repo_item_key).execute()[0]:
                    continue

                repos_to_add = [{
                    'name': repo.name,
                    'description': repo.description,
                    'uri': repo.uri,
                    'tags': label_names
                }]

        for repo in repos_to_add:
            key = cache_key_delimiter.join([repo_key, repo.pop('name')])
            pipe.hmset(key, repo)

        for label in labels_to_add:
            pipe.zadd(*label)

        pipe.execute()

    logger.debug('Labels({}) are added to cache.'.format([label[0] for label in labels_to_add]))
    logger.debug('Repos({}) added to cache.'.format(repo_names))


def add_repos(redis, cache_key, tags, repos):
    tags = tags or []
    repos = repos or []

    label_key = cache_key_delimiter.join([cache_key, 'labels'])
    repo_key = cache_key_delimiter.join([cache_key, 'repos'])
    tag_key = cache_key_delimiter.join([cache_key, 'tags'])

    with redis.pipeline() as pipe:
        # increment the popularity of tags
        for tag in tags:
            pipe.zincrby(tag_key, tag)

        # TODO: use itertools if you can
        for repo in repos:
            labels = [label.name for label in repo.labels]
            to_update_tags = set(labels).intersection(tags)

            for tag in to_update_tags:
                label_item_key = cache_key_delimiter.join([label_key, tag])
                pipe.zadd(label_item_key, repo.downloads, repo.name)

            key = cache_key_delimiter.join([repo_key, repo.name])
            pipe.hmset(key, {
                'description': repo.description,
                'uri': repo.uri,
                'tags': [tag.name for tag in repo.labels]
            })

        pipe.execute()


def get_repos_from_tags(redis, cache_key, tags=None):
    tags = tags or [name for name, download in get_tags(redis, cache_key, tags)[0]]

    logger.debug('Get the repos for Tags({}) from cache.'.format(tags))

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

                repo_names = [repo[0] for repo in repos_per_tag]
                logger.debug('Repos({}) under Label({}).'.format(repo_names, label_item_key))

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

        pipe.execute()

    logger.debug('Repos({}) added in cache. Non Cahed Tags({})'.format(result, non_cached_tags))

    return result, non_cached_tags


def get_repo_details(redis, cache_key, repo):
    key = cache_key_delimiter.join([cache_key, 'repos', repo])
    details = redis.hgetall(key)

    if details:
        logger.debug('Repo({}) Details({}) are fetched from cache.'.format(repo, details))

    return details
