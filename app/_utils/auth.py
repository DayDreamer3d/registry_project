import functools
import flask
import redis
import uuid
from . import config


config = config.get_config()


def add_client_key():
    redis_server = redis.StrictRedis.from_url(config['REDIS_URIS']['app'])
    key = config['CACHE']['DELIMITER'].join([
        config['CACHE']['KEY'],
        'client',
    ])
    name = uuid.uuid4().hex
    value = float(redis_server.time()[0])
    redis_server.zadd(key, value, name)
    return name


def validate_client_key(client_key, ttl=86400):
    redis_server = redis.StrictRedis.from_url(config['REDIS_URIS']['app'])

    key = config['CACHE']['DELIMITER'].join([
        config['CACHE']['KEY'],
        'client'
    ])

    creation_time = redis_server.zscore(key, client_key)
    if creation_time is None:
        return False

    current_time = redis_server.time()[0]

    if current_time - creation_time < ttl:
        return True

    redis_server.zrem(key, client_key)
    return False


def validate_client(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        client_key = flask.request.args.get('client-key')
        if not (client_key and validate_client_key(client_key)):
            response = {
                'error': 'unauthorised',
                'message': 'Unauthorised client. Please generate new Client Key.',
                'key-generator-url': '{}/auth/client-key'.format(flask.url_for('api_home'))
            }
            return flask.make_response(
                flask.jsonify(response),
                401,
                {
                    'WWW-Authenticate': 'CustomBasic realm="Authentication Required"',
                    'Location': '{}/auth/client-key'.format(flask.url_for('api_home'))
                }
            )
        return func(*args, **kwargs)
    return wrapper
