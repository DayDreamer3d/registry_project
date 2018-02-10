""" Utility module for all the database related queries.
"""

import logging

from . import models as _models


service_name = 'registry'
logger = logging.getLogger('services_{}'.format(service_name))


# TODO: make these functions as methods,
# be careful class may hold state for "session" var.
def add_tags(session, tags):
    """ Add the tags to the db.

        Args:
            session (session object): db session object.
            tags (list): list of tags to be added in db.
    """
    tag_objs = [_models.Tag(name=tag, popularity=1) for tag in tags]
    session.add_all(tag_objs)
    session.commit()

    logger.debug('Tags() are added to db.'.format(tags))


def update_popularity(session, tags):
    """ Update the given tags popularity.

        Args:
            session (session object): db session object.
            tags (list): list of tags to be updated.
    """
    tag_counts = {}
    for tag in tags:
        if tag not in tag_counts.keys():
            tag_counts[tag] = tags.count(tag)

    tags = session.query(_models.Tag)\
        .filter(_models.Tag.name.in_(tag_counts.keys()))\
        .all()

    for tag in tags:
        tag.popularity = _models.Tag.popularity + tag_counts[tag.name]

    session.commit()


def get_tags(session, tags=None):
    """ Get the tags from the db.

        Args:
            session (session object): db session object.
            tags (list): list of tags to be fetched from in db.
                        None means fetch all tags.

        Returns:
            (list): list of tags details fetched from db.
    """
    tags = tags or []
    tag_objs = []

    if tags:
        tag_objs = session.query(_models.Tag)\
            .filter(_models.Tag.name.in_(tags))\
            .order_by(_models.Tag.popularity.desc())\
            .all()
    else:
        tag_objs = session.query(_models.Tag)\
            .order_by(_models.Tag.popularity.desc())\
            .all()

    tag_names = [tag.name for tag in tag_objs]
    logger.debug('Tags({}) are fetched from db.'.format(tag_names))

    return tag_objs


def add_repos(session, repos):
    """ Add the given repositores to the db.

        Args:
            session (session object): db session object.
            repos (list): list of repositories need to be updated in the db.
    """

    added_repos = []

    for repo in repos:
        repo_obj = _models.Repository(
            name=repo['name'],
            description=repo['description'],
            uri=repo['uri']
        )
        session.add(repo_obj)

        for tag in repo['tags']:
            tag = session.query(_models.Tag)\
                    .filter(_models.Tag.name == tag)\
                    .first()
            repo_obj.labels.append(tag)

        added_repos.append(repo_obj)

    session.commit()

    repo_names = [repo.name for repo in added_repos]
    logger.debug('Repos({}) are added to db.'.format(repo_names))

    return added_repos


def update_downloads(session, repos):
    """ Update the repository's downlaod attribute in db.

        Args:
            session (session object): db session object.
            repos (list): list of repositores to be updated.
    """
    repos = session.query(_models.Repository)\
        .filter(_models.Repository.name.in_(repos))\
        .all()
    for repo in repos:
        repo.downloads = _models.Repository.downloads + 1
    session.commit()


def get_repos_from_tags(session, tags=None):
    """ Fetch repositores for the given tags.

        Args:
            session (session object): db session object.
            tags (list): repositores will be fetched based on these given tags.

        Returns:
            list: of repositories fetched from db.
    """
    if not tags:
        return []

    tag_ids = [tag.id_ for tag in get_tags(session, tags)]
    repos = session.query(_models.Repository)\
        .filter(_models.Repository.labels.any(
            _models.Tag.id_.in_(tag_ids)))\
        .order_by(_models.Repository.downloads.desc())\
        .all()

    repo_names = [repo.name for repo in repos]
    logger.debug('Repos({}) are fetched from db for Tags({}).'.format(repo_names, tags))

    return repos


def get_repo_details(session, repo):
    """ Get detail for the given repository.

        Args:
            session (session object): db session object.
            repo (str): repository name for which details will be fetched.

        Returns:
            (dict): details for the given repository.

    """
    return session.query(_models.Repository)\
        .filter(_models.Repository.name == repo)\
        .first()
