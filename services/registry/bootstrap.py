import random

# import nameko
# from nameko.standalone import rpc
import sqlalchemy
from sqlalchemy.orm import sessionmaker
import sqlalchemy_utils

from .._utils import config
from ._impl import registry
from ._impl.orm import models, query


def create_db():
    # get the config
    service_config = config.get_config(registry.service_name)

    # create the db, sqlachemy doesn't create db
    engine = sqlalchemy.create_engine(
        registry.RegistryService.config['DB_URIS']['registry:Base']
    )
    if sqlalchemy_utils.database_exists(engine.url):
        sqlalchemy_utils.drop_database(engine.url)
    sqlalchemy_utils.create_database(engine.url)


def insert_data():

    repos = {
        'alembic-base': {
            'description': 'The base of alembic caches.',
            'downloads': 342,
            'uri': 'alembic-base.v1',
            'tags': [
                '"alembic file format"',
                '"vfx pipeline"'
            ]
        },
        'usd_dev:v2': {
            'description': 'Second version of USD in Docker development.',
            'downloads': 250,
            'uri': 'usd_dev.v2',
            'tags': [
                'docker usd',
                '"vfx pipeline"'
            ]
        },
        'usd_dev:anim': {
            'description': 'Production version of USD in Docker for feature animation pipeline.',
            'downloads': 410,
            'uri': 'usd_dev.anim',
            'tags': [
                'docker usd',
            ]
        },
        'nodes editor': {
            'description': 'Generic Qt Node editor.',
            'downloads': 500,
            'uri': 'nodes_editor.v1',
            'tags': [
                'node graph qt',
                '"vfx pipeline"'
            ]
        },
        'usd_standalone': {
            'description': 'Standalone USD workflow.',
            'downloads': 467,
            'uri': 'usd_standalone.v1',
            'tags': [
                '"universal scene description"',
                '"vfx pipeline"'
            ]
        },
    }

    tags = []
    for repo, info in repos.items():
        tags.extend(info['tags'])
    tags = set(tags)

    engine = sqlalchemy.create_engine(
        registry.RegistryService.config['DB_URIS']['registry:Base']
    )
    db_session = sessionmaker(bind=engine)()
    with query.session_scope(db_session) as db_session:
        tags = [
            models.Tag(name=tag, popularity=random.randint(1, 10))
            for tag in tags
        ]
        db_session.add_all(tags)

        for repo, info in repos.items():
            repo = models.Repository(
                name=repo,
                description=info['description'],
                downloads=info['downloads'],
                uri=info['uri']
            )
            db_session.add(repo)

            for tag in info['tags']:
                tag = db_session.query(models.Tag).filter(models.Tag.name == tag).one()
                repo.items.append(tag)


if __name__ == '__main__':
    create_db()

    container = registry.create_container()

    # starting the service will create the tables
    container.start()

    # insert the data
    insert_data()

    container.wait()
