import functools
import flask
import redis
import uuid
from . import config


config = config.get_config()


def add_client_key():
    redis_server = redis.StrictRedis.from_url(config['REDIS_URIS']['app'])
    key = config['CACHE']['DELIMITER'].join(
        cache['CACHE']['KEY'],
        'client',
    )
    return redis.zadd(key, uuid.uuid4().hex, redis.time()[0])


def validate_client_key(client_key, ttl=86400):
    redis_server = redis.StrictRedis.from_url(config['REDIS_URIS']['app'])

    key = config['CACHE']['DELIMITER'].join(
        cache['CACHE']['KEY'],
        'client',
    )

    creation_time = redis.zscore(key, client_key)
    if creation_time is None:
        return False

    current_time = redis.time()[0]

    if creation_time + ttl < current_time:
        return True

    redis.zrm(client_key)
    return False


def validate_client(func):
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        client_key = request.args.get('client_key')
        if not (client_key and validate_client_key(client_key)):
            response = {
                'error': 'unauthorised',
                'message': 'Unauthorised client. Please generate new Client Key.',
                'key-generator': '/api/auth/client-key'
            }
            return flask.make_response(
                flask.jsonify(response),
                401,
                {
                    'WWW-Authenticate': 'CustomBasic realm="Authentication Required"',
                    'Location': '/api/auth/client-key'
                }
            )
        return func(*args, **kwargs)
    return func
