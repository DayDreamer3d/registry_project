import contextlib
from nameko_sqlalchemy import database
import sqlalchemy
import sqlalchemy_utils


class DbSession(database.Session):
    def setup(self):
        super().setup()
        self.declarative_base.metadata.create_all(self.engine)


@contextlib.contextmanager
def session_scope(session):
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_db(url):
    engine = sqlalchemy.create_engine(url)
    if sqlalchemy_utils.database_exists(engine.url):
        sqlalchemy_utils.drop_database(engine.url)
    sqlalchemy_utils.create_database(engine.url)
