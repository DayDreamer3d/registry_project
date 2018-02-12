""" Service entrypoint for docker compose which also act as a bootstrap for service.
"""

from .._utils import config
from ._impl import service

import sqlalchemy
import sqlalchemy_utils


def create_db():
    """ Create the database for the service on db server.
    """
    # create the db, sqlachemy doesn't create db
    engine = sqlalchemy.create_engine(service.config['DB_URIS']['registry:Base'])
    if sqlalchemy_utils.database_exists(engine.url):
        sqlalchemy_utils.drop_database(engine.url)
    sqlalchemy_utils.create_database(engine.url)


if __name__ == '__main__':
    create_db()

    # create service container
    container = service.create_container()

    # starting the service will create the tables
    container.start()

    # keep the service running
    container.wait()
