import nameko
from nameko.standalone import rpc
import sqlalchemy
import sqlalchemy_utils

from .._utils import config
from ._impl import registry

# service_name =


def create_db():
    # get the config
    service_config = config.get_config(registry.service_name)

    # create the db, sqlachemy doesn't create db
    engine = sqlalchemy.create_engine(
        registry.RegistryService.config
        # service_config['DB_URIS']['registry:Base']
    )
    if sqlalchemy_utils.database_exists(engine.url):
        sqlalchemy_utils.drop_database(engine.url)
    sqlalchemy_utils.create_database(engine.url)


def insert_data():
    repos = {
        'alembic-base': {
            'description': 'The base of alembic caches.',
            'downloads': 342,
            'url': '/',
            'tags': [
                '"alembic file format"',
                '"vfx pipeline"'
            ]
        },
        'usd_dev:v2': {
            'description': 'Second version of USD in Docker development.',
            'downloads': 250,
            'url': '/',
            'tags': [
                'docker usd',
                '"vfx pipeline"'
            ]
        },
        'usd_dev:anim': {
            'description': 'Production version of USD in Docker for feature animation pipeline.',
            'downloads': 410,
            'url': '/',
            'tags': [
                'docker usd',
            ]
        },
        'nodes editor': {
            'description': 'Generic Qt Node editor.',
            'downloads': 500,
            'url': '/',
            'tags': [
                'node graph qt',
                '"vfx pipeline"'
            ]
        },
        'usd_standalone': {
            'description': 'Standalone USD workflow.',
            'downloads': 467,
            'url': '/',
            'tags': [
                '"universal scene description"',
                '"vfx pipeline"'
            ]
        },
    }

    # add initial data using a service
    with rpc.ServiceProxy(
        registry.service_name,
        registry.RegistryService.config
    ) as cluster_rpc:
        cluster_rpc.registry.add_repos(repos)


if __name__ == '__main__':
    create_db()
    container = registry.create_container()
    container.start()
    insert_data()
    container.wait()
