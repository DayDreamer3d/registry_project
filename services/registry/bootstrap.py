import random

import sqlalchemy
from sqlalchemy.orm import sessionmaker

from .._utils import config, db
from ._impl import service, models


def create_db():
    # create the db, sqlachemy doesn't create db
    db.create_db(service.config['DB_URIS']['registry:Base'])


def insert_data():

    repos = [
        {'alembic-base': {
            'description': 'The base of alembic caches.',
            'downloads': 342,
            'uri': 'alembic-base.v1',
            'tags': [
                '"alembic file format"',
                '"vfx pipeline"'
            ]
        }},
        {'usd_dev:v2': {
            'description': 'Second version of USD in Docker development.',
            'downloads': 250,
            'uri': 'usd_dev.v2',
            'tags': [
                'docker usd',
                '"vfx pipeline"'
            ]
        }},
        {'usd_dev:anim': {
            'description': 'Production version of USD in Docker for feature animation pipeline.',
            'downloads': 410,
            'uri': 'usd_dev.anim',
            'tags': [
                'docker usd',
            ]
        }},
        {'nodes editor': {
            'description': 'Generic Qt Node editor.',
            'downloads': 500,
            'uri': 'nodes_editor.v1',
            'tags': [
                'node graph qt',
                '"vfx pipeline"'
            ]
        }},
        {'usd_standalone': {
            'description': 'Standalone USD workflow.',
            'downloads': 467,
            'uri': 'usd_standalone.v1',
            'tags': [
                '"universal scene description"',
                '"vfx pipeline"'
            ]
        }},
    ]

    tags = []
    for repo_info in repos:
        for repo, info in repo_info.items():
            tags.extend(info['tags'])
    tags = list(set(tags))

    engine = sqlalchemy.create_engine(
        service.RegistryService.config['DB_URIS']['registry:Base']
    )

    db_session = sessionmaker(bind=engine)()
    with db.session_scope(db_session) as db_session:
        tags = [
            models.Tag(name=tag, popularity=random.randint(1, 10))
            for tag in tags
        ]
        db_session.add_all(tags)

        for repo_info in repos:
            for repo, info in repo_info.items():
                repo = models.Repository(
                    name=repo,
                    description=info['description'],
                    downloads=info['downloads'],
                    uri=info['uri']
                )
                db_session.add(repo)

                for tag in info['tags']:
                    tag = db_session.query(models.Tag).filter(models.Tag.name == tag).one()
                    repo.labels.append(tag)


if __name__ == '__main__':
    create_db()

    # create service container
    # container = service.create_container()

    # starting the service will create the tables
    # container.start()

    # insert the data
    # insert_data()

    # keep the service running
    # container.wait()
