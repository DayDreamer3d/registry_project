import sqlalchemy
from sqlalchemy.ext import declarative


class Base(object):
    pass


DeclarativeBase = declarative.declarative_base(cls=Base)


repositories_tags = sqlalchemy.Table(
    'repositories_tags',
    DeclarativeBase.metadata,
    sqlalchemy.Column(
        'tag_id',
        sqlalchemy.Integer,
        sqlalchemy.ForeignKey('tags.id_')
    ),
    sqlalchemy.Column(
        'repo_id',
        sqlalchemy.Integer,
        sqlalchemy.ForeignKey('repositories.id_')
    ),
)


class Tag(DeclarativeBase):
    __tablename__ = 'tags'

    id_ = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String(30), unique=True)
    popularity = sqlalchemy.Column(sqlalchemy.Integer, default=lambda: 0)
    association = sqlalchemy.orm.relationship(
        'Repository',
        secondary=repositories_tags,
        backref=sqlalchemy.orm.backref('items', lazy='dynamic')
    )


class Repository(DeclarativeBase):
    __tablename__ = 'repositories'

    id_ = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String(100), unique=True)
    description = sqlalchemy.Column(sqlalchemy.String(500))
    downloads = sqlalchemy.Column(sqlalchemy.Integer, default=lambda: 0)
    uri = sqlalchemy.Column(sqlalchemy.String(500), unique=True)
