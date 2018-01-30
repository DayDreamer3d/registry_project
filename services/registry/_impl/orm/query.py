from contextlib import contextmanager
import nameko_sqlalchemy

from . import models as _models


@contextmanager
def session_scope(session):
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_tags(session, tags=None):
    """ Get the tags from the db.

        Args:
    """
    with session_scope(session) as session:
        if tags:
            return session.query(_models.Tag)\
                .filter(_models.Tag(tags))\
                .order_by(_models.Tag.popularity.desc())\
                .all()
        else:
            return session.query(_models.Tag)\
                .order_by(_models.Tag.popularity.desc())\
                .all()


def add_repos(session, repos):
    with session_scope(session):
        tags = set()
        for repo, info in repos.items():
            repo = _models.Repository(
                name=repo,
                description=info['description'],
                downloads=info['downloads'],
                url=info['url']
            )
            session.add(repo)

            # only add unique tags
            tags.add([_models.Tag(name=tag) for tag in set(info['tags'])])
            session.add_all(tags)

            for tag in tags:
                repo.items.append(tag)



def get_repos(tags=None):
    with session_scope(session) as session:
        pass
