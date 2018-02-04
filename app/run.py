import flask
import flask_nameko
from urllib import parse
from _utils import config, auth

config = config.get_config()

rpc = flask_nameko.FlaskPooledClusterRpcProxy()

app = flask.Flask(__name__)
app.config['NAMEKO_AMQP_URI'] = config['NAMEKO_AMQP_URI']
# app.config['SERVER_NAME'] = 'software-registry.com'

rpc.init_app(app)


# TODO: use cache here of redis
@app.route('/', methods=['GET', 'POST'])
def index():
    return 'Yeah !!'


@app.route('/api', methods=['GET'])
def api_home():
    api_home_url = flask.url_for('api_home')
    resources = ['repos', 'tags']
    response = {
        '{}-url'.format(resource): '{}/{}'.format(api_home_url, resource)
        for resource in resources
    }
    return flask.jsonify(response)


@app.route('/api/tags', methods=['GET', 'POST'])
@auth.validate_client
def tags():
    if flask.request.method == 'GET':
        return get_tags()
    elif flask.request.method == 'POST':
        return add_tag()


@app.route('/api/tags/<path:tag>', methods=['GET'])
@auth.validate_client
def get_tag(tag):
    tags = rpc.registry.get_tags([tag])
    for name, popularity in tags:
        tag = {'name': name, 'popularity': popularity}
        return flask.jsonify(tag)

    response = {
        'error': 'Not Found',
        'message': '{} tag not found. Visit tags url to get a list of all the valid tags.'.format(tag),
        'tags-url': flask.url_for('tags')
    }
    return flask.make_response(
        flask.jsonify(response),
        404,
        {'Location': flask.url_for('tags')}
    )


@app.route('/api/repos', methods=['GET', 'POST'])
@auth.validate_client
def repos():
    if flask.request.method == 'GET':
        return get_repos()
    elif flask.request.method == 'POST':
        return add_repo()


@app.route('/api/repos/<path:repo>', methods=['GET'])
@auth.validate_client
def get_repo(repo):
    repo = rpc.registry.get_repo(repo)
    if repo:
        return flask.jsonify(repo)

    response = {
        'error': 'Not Found',
        'message': '{} repo not found. Visit repos url to get a list of all the valid repos.'.format(tag),
        'repos-url': flask.url_for('repos')
    }
    return flask.make_response(
        flask.jsonify(response),
        404,
        {'Location': flask.url_for('repos')}
    )


@app.route('/api/auth/client-key', methods=['POST'])
def generate_client_key():
    response = {
        'client-key': auth.add_client_key(),
        'api-home': flask.url_for('api_home'),
        'client-key-example': '{}/repos?client_key=xxxxx&param="param1"'.format(flask.url_for('api_home'))
    }
    return flask.jsonify(response)


def add_tag():
    try:
        name = flask.request.get_json(force=True)
    except Exception as e:
        # TODO: log exception
        response = {
            'error': 'malformed request',
            'message': 'Request body is not json serialisable. Use a json object with name field e.g. {"name": "tag name"}',
        }
        return flask.make_response(
            flask.jsonify(response),
            400,
            {}
        )

    name = name.get('name')
    if not name:
        response = {
            'error': 'missing parameter',
            'message': 'No tag name provided in the request body. Use a json object with name field e.g. {"name": "tag name"}',
        }
        return flask.make_response(
            flask.jsonify(response),
            422,
            {}
        )

    rpc.registry.add_tags([name])

    tag_url = parse.quote('{}/{}'.format(flask.url_for('tags'), name))

    response = {
        'message': '"{}" tag has been created.'.format(name),
        'new-tag-url': tag_url
    }
    return flask.make_response(
        flask.jsonify(response),
        201,
        {'Location': tag_url}
    )


def get_tags():
    tags = {
        name: parse.quote('/'.join([flask.url_for('tags'), name]))
        for name, popularity in rpc.registry.get_tags()
    }
    tags = {'tag-urls': tags}
    return flask.jsonify(tags)


def add_repo():
    required_keys = ['name', 'description', 'uri', 'tags']
    try:
        repo = flask.request.get_json(force=True)
    except Exception as e:
        # TODO: log exception
        keys_str = ', '.join(required_keys)
        response = {
            'error': 'malformed request',
            'message': 'Request body is not json serialisable. Use a json object with fields: {}'.format(keys_str)
        }
        return flask.make_response(
            flask.jsonify(response),
            400,
            {}
        )

    missing_keys = set(required_keys).difference(repo.keys())
    if missing_keys:
        missing_keys = ', '.join(missing_keys)
        keys_str = ', '.join(required_keys)
        response = {
            'error': 'missing parameter',
            'message': 'Request body is missing {} keys. Use a json object with fields: {}.'.format(missing_keys, keys_str),
        }
        return flask.make_response(
            flask.jsonify(response),
            422,
            {}
        )

    name = repo.pop('name')
    repo = {name: repo}

    rpc.registry.add_repos([repo])

    repo_url = parse.quote(
        '{}/{}'.format(flask.url_for('repos'), name)
    )

    response = {
        'message': '"{}" repo has been created.'.format(name),
        'new-tag-url': repo_url
    }
    return flask.make_response(
        flask.jsonify(response),
        201,
        {'Location': repo_url}
    )


def get_repos():
    repos = {
        repo['name']: parse.quote('/'.join([flask.url_for('repos'), repo['name']]))
        for repo in rpc.registry.get_repos(flask.request.args.getlist('tag'))
    }
    return flask.jsonify({
        'repo-urls': repos,
        'tags-query-example': '{}?tag=tag1&tag=tag2'.format(flask.url_for('repos')),
    })


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
