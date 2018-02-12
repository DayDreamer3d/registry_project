""" Service entrypoint for docker compose which also act as a bootstrap for service.
"""

from .._utils import config, db
from ._impl import service


def create_db():
    """ Create the database for the service on db server.
    """
    # create the db, sqlachemy doesn't create db
    db.create_db(service.config['DB_URIS']['registry:Base'])


if __name__ == '__main__':
    create_db()

    # create service container
    container = service.create_container()

    # starting the service will create the tables
    container.start()

    # keep the service running
    container.wait()
