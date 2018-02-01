import collections
# import redis

# from nameko_redis import Redis


cache_key_delimiter = ':'

# REVIEW: what about having cache as a service

def add_tags(redis, cache_key, tags):
    key = cache_key_delimiter.join([cache_key, 'tags'])

    items = []
    for tag in tags:
        items.append(tag[0])  # tag name
        items.append(int(tag[1]))  # popularity as score

    with redis.pipeline() as pipe:
        pipe.zadd(key, *items).execute()


def get_tags(redis, cache_key):
    key = cache_key_delimiter.join([cache_key, 'tags'])
    with redis.pipeline() as pipe:
        tags = pipe.zrevrangebyscore(key, '+inf', 0, withscores=True).execute()
        return [
            (tag.decode(), int(popularity))
            for tag, popularity in tags[0]
        ]


def add_repos(redis, cache_key, repos):
    label_key = cache_key_delimiter.join([cache_key, 'labels'])
    repo_key = cache_key_delimiter.join([cache_key, 'repos'])
    tag_key = cache_key_delimiter.join([cache_key, 'tags'])

    # search how many tags are in cache
    with redis.pipeline() as pipe:
        for repo in repos:
            tags_in_cache = False

            for tag in repo.labels:
                # intenionally using redis than pipeline
                # because pipeline will buffer the below commands
                # and will execute the first buffered command here
                # which would give the undesired result
                # TODO: look deep in pipelining and find solution
                if redis.zrank(tag_key, tag.name) is not None:
                    tags_in_cache = True

                    # update popularity for tag
                    pipe.zincrby(tag_key, tag.name)

                    # add label, mapping between tag and repo
                    label_item_key = cache_key_delimiter.join([label_key, tag.name])
                    pipe.zadd(label_item_key, repo.name, repo.downloads)

            if not tags_in_cache:
                continue

            # only add repo, if one of the tag is in cache
            key = cache_key_delimiter.join([repo_key, repo.name])
            pipe.hmset(
                key, {
                    'description': repo.description,
                    'uri': repo.uri
                }
            )

            pipe.execute()


def get_repos(redis, cache_key, tags):
    label_key = cache_key_delimiter.join([cache_key, 'labels'])
    repo_key = cache_key_delimiter.join([cache_key, 'repos'])
    tag_key = cache_key_delimiter.join([cache_key, 'tags'])

    non_cached_tags = []
    result = []
    with redis.pipeline() as pipe:
        # get repos per tag basis
        # use list to maintain the order
        repos = []
        for tag in tags:
            label_item_key = cache_key_delimiter.join([label_key, tag])
            repos_per_tag = pipe.zrevrangebyscore(
                label_item_key, '+inf', 0, withscores=True).execute()
            repos_per_tag = repos_per_tag[0]

            # if tag doesn't exists in cache
            # skip it and eventually get its result from db
            if repos_per_tag:
                for r in repos_per_tag:
                    if r not in repos:
                        repos.append(r)
            else:
                non_cached_tags.append(tag)

        for repo, downloads in repos:
            repo = repo.decode()
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

    return result, non_cached_tags
