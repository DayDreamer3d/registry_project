import nameko_sqlalchemy

from . import models as _models

# TODO: make these functions as methods,
# be careful class may hold state for "session" var.
def add_tags(session, tags=None):
    """ Add the tags to the db.

        Args:
    """
    tags = [_models.Tag(name=tag, popularity=1) for tag in tags]
    session.add_all(tags)
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
