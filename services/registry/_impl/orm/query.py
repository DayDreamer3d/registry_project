import nameko_sqlalchemy

from . import models as _models

# TODO: make these functions as methods,
# be careful class may hold state for "session" var.
def add_tags(session, tags):
    """ Add the tags to the db.

        Args:
    """
    tags = [_models.Tag(name=tag, popularity=1) for tag in tags]
    session.add_all(tags)
    session.commit()
    # TODO:  Update cache


def update_popularity(session, tags):
    """ Update the tags to the db.

        Args:
    """
    tag_counts = {}
    for tag in tags:
        if tag not in counts.keys():
            tag_counts[tag] = tags.count(tag)

    tags = session.query(_models.Tags)\
        .filter(_models.Tag.name.in_(tag_counts.keys()))\
        .all()

    for tag, count in tag_counts.items():
        tag.popularity = _models.Tags.popularity + count

    session.commit()


def get_tags(session, tags=None):
    """ Get the tags from the db.

        Args:
    """
    if tags:
        return session.query(_models.Tag)\
            .filter(_models.Tag.name.in_(tags))\
            .order_by(_models.Tag.popularity.desc())\
            .all()
    else:
        return session.query(_models.Tag)\
            .order_by(_models.Tag.popularity.desc())\
            .all()


def add_repos(session, repos):
    added_repos = []
    for repo in repos:
        for name, info in repo.items():
            repo_obj = _models.Repository(
                name=name,
                description=info['description'],
                downloads=info['downloads'],
                uri=info['uri']
            )
            session.add(repo_obj)

            for tag in info['tags']:
                tag = session.query(_models.Tag)\
                        .filter(_models.Tag.name == tag)\
                        .one()
                repo_obj.labels.append(tag)

            added_repos.append(repo_obj)
    session.commit()

    return added_repos


def update_downloads(session, repos):
    """ Update the repos to the db.

        Args:
    """
    repos = session.query(_models.Repository)\
        .filter(_models.Repository.name.in_(repos))\
        .all()
    for repo in repos:
        repo.downloads = _models.Repository.downloads + 1
    session.commit()


def get_repos(session, tags=None):
    if tags:
        # session.query(_models.labels)\
        # .filter(_models.labels.tag_id.in_(tags))
        tag_ids = [tag.id_ for tag in get_tags(session, tags)]
        return session.query(_models.labels)\
            .filter(_models.labels.tag.id_.in_(tags))\
            .all()
            # .order_by(_models.Repository.downloads.desc())\
    else:
        return session.query(_models.Repository)\
            .order_by(_models.Repository.downloads.desc())\
            .all()
