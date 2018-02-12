""" Utility module for database.
"""

import contextlib
import nameko_sqlalchemy
import sqlalchemy
import sqlalchemy_utils


class DbSession(nameko_sqlalchemy.Session):
    """ Class to create the db session for trasactions.
    """
    def setup(self):
        """ Method to setup the db i.e. create all componenets of it.
        """
        super().setup()
        self.declarative_base.metadata.create_all(self.engine)


def create_db(url):
    """ Function to create the database.

        Args:
            url (str): url for the database.
    """
    engine = sqlalchemy.create_engine(url)
    if sqlalchemy_utils.database_exists(engine.url):
        sqlalchemy_utils.drop_database(engine.url)
    sqlalchemy_utils.create_database(engine.url)
