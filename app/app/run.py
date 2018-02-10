""" Main app module sitting at frontend
and providing all the api entrypoints and rendering templates.
"""

import functools
import flask
import flask_nameko
from urllib import parse
from _utils import config, auth

config = config.get_config()

rpc = flask_nameko.FlaskPooledClusterRpcProxy()

app = flask.Flask(__name__)
app.config['NAMEKO_AMQP_URI'] = config['NAMEKO_AMQP_URI']

rpc.init_app(app)

# TODO: use Blueprint for different routes


@app.errorhandler(404)
def resource_not_found(category, resource):
    """ Custom 404 error handlder
    """
    response = {'error': 'Resource not found.'}
    response['message'] = '{title}({resource}) not found. Visit {category} url for all the resources.'.format(
        title=category.title(), resource=resource, category=category
    )

    url = flask.url_for(category)
    response['{}_url'.format(category)] = url

    return flask.make_response(
        flask.jsonify(response),
        404,
        {'Location': url}
    )


def client_key_from_cookie(func):
    """ Decorator to get client key from cookie.

        Args:
            func: function object

        Returns:
            Function object
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        """ Wrapper function to the actual work

            Args:
                args(list): all the required arguments.

            Kwargs:
                kwargs(dict): all the keyword arguments.

            Returns:
                output of the wrapped function.
        """
        cookie_key = 'software-registry-client-key'
        client_key = flask.request.cookies.get(cookie_key)
        kwargs['client_key'] = client_key
        return func(*args, **kwargs)
    return wrapper


@app.route('/', methods=['GET', 'POST'])
@client_key_from_cookie
@auth.validate_client
def index(client_key=None):
    """ Entryoint for the ui.

        Kwargs:
            client-key: user provding the unique client key (per session).

        Returns:
            Response object: response object containg renderend template and client-key cookie.
    """
    response = flask.make_response('Test cookie: {}'.format(client_key))
    if not client_key:
        client_key = auth.add_client_key()

    tags = [name for name, _ in rpc.registry.get_tags()]

    response = flask.make_response(
        flask.render_template('index.html', tags=tags, repos=[])
    )

    response.set_cookie('software-registry-client-key', client_key)

    return response


@app.route('/repo_cards', methods=['GET'])
@client_key_from_cookie
@auth.validate_client
def get_repo_cards(client_key=None):
    """ Render the repository cards.

        Kwargs:
            client-key: user provding the unique client key (per session).

        Returns:
            Response object: response object containg renderend template and client-key cookie.
    """
    response = flask.make_response('Test cookie: {}'.format(client_key))
    if not client_key:
        client_key = auth.add_client_key()

    tags = flask.request.args.getlist('tag')

    repos = rpc.registry.get_repos(tags)

    response = flask.make_response(
        flask.render_template('repo_cards.html', repos=repos)
    )

    response.set_cookie('software-registry-client-key', client_key)

    return response


@app.route('/api', methods=['GET'])
def api_home():
    """ Home entrypoint for the api.

        Returns:
            Response object: with all the categories of resources.
    """
    api_home_url = flask.url_for('api_home')
    resources = ['repos', 'tags']
    response = {
        '{}_url'.format(resource): '{}/{}'.format(api_home_url, resource)
        for resource in resources
    }
    response['client_key_url'] = '{}/auth/client-key'.format(flask.url_for('api_home'))
    return flask.jsonify(response)


@app.route('/api/tags', methods=['GET', 'POST'])
@auth.validate_client
def tags():
    """ Entrypoint to get/set the tags/tag.

        Returns:
            Response object: json response for the operation.
    """
    if flask.request.method == 'GET':
        return get_tags()
    elif flask.request.method == 'POST':
        return add_tag()


@app.route('/api/tags/<path:tag>', methods=['GET'])
@auth.validate_client
def get_tag(tag):
    """ Entrypoint to get the details of a tag.

        Args:
            tag: required tag for which the details will be fetched.

        Returns:
            Response object: json response with tag details.
    """
    tags = rpc.registry.get_tags([tag])
    for name, popularity in tags:
        tag = {'name': name, 'popularity': popularity}
        return flask.jsonify(tag)
    return resource_not_found('tags', tag)


@app.route('/api/repos', methods=['GET', 'POST'])
@auth.validate_client
def repos():
    """ Entrypoint to get/set the repositories/repository.

        Returns:
            Response object: json response for the operation.
    """
    if flask.request.method == 'GET':
        return get_repos()
    elif flask.request.method == 'POST':
        return add_repo()


@app.route('/api/repos/<path:repo>', methods=['GET', 'PUT'])
@auth.validate_client
def get_repo(repo):
    """ Entrypoint to get the details of a repository.

        Args:
            repo: required repository for which the details will be fetched.

        Returns:
            Response object: json response with repository details.
    """
    if flask.request.method == 'GET':
        return get_repo_details(repo)
    elif flask.request.method == 'PUT':
        return update_downloads(repo)


@app.route('/api/auth/client-key', methods=['POST'])
def generate_client_key():
    """ Entrypoint to generate the client key.

        Returns:
            Response object: json response with client key.
    """
    response = {
        'client_key': auth.add_client_key(),
        'api_home': flask.url_for('api_home'),
        'client_key_example': '{}/repos?client_key=xxxxx&param="param1"'.format(flask.url_for('api_home'))
    }
    return flask.jsonify(response)


def add_tag():
    """ Function to add a tag to the registry.

        Returns:
            Response object: json response with url for the tag.
    """
    try:
        name = flask.request.get_json(force=True)
    except Exception as e:
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
        'new_tag_url': tag_url
    }
    return flask.make_response(
        flask.jsonify(response),
        201,
        {'Location': tag_url}
    )


def get_tags():
    """ Function to fetch tags from registry.

        Returns:
            Response object: json response with all urls for the fetched tags.
    """
    tags = rpc.registry.get_tags()

    tag_urls = {
        name: parse.quote('/'.join([flask.url_for('tags'), name]))
        for name, popularity in tags
    }

    response = {
        'tag_details': tags,
        'tag_urls': tag_urls
    }

    return flask.jsonify(response)


def add_repo():
    """ Function to add a repository to the registry.

        Returns:
            Response object: json response with url for the repository.
    """
    required_keys = ['name', 'description', 'uri', 'tags']
    try:
        repo = flask.request.get_json(force=True)
    except Exception as e:
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

    rpc.registry.add_repos([repo])

    repo_url = parse.quote(
        '{}/{}'.format(flask.url_for('repos'), repo['name'])
    )

    response = {
        'message': '"{}" repo has been created.'.format(repo['name']),
        'new_repo_url': repo_url
    }
    return flask.make_response(
        flask.jsonify(response),
        201,
        {'Location': repo_url}
    )


def get_repos():
    """ Function to fetch repositories from registry.

        Returns:
            Response object: json response with all urls for the fetched repositories.
    """
    tags = flask.request.args.getlist('tag')

    repos = rpc.registry.get_repos(tags)

    repo_urls = {
        repo['name']: parse.quote('/'.join([flask.url_for('repos'), repo['name']]))
        for repo in repos
    }

    response = {
        'repo_details': repos,
        'repo_urls': repo_urls
    }
    if not tags:
        response['repo_query_example'] = '{}?tag=tag1&tag=tag2'.format(flask.url_for('repos'))

    return flask.jsonify(response)


def get_repo_details(repo):
    """ Function to get details of given repository.

        Args:
            repo: required repository for which the details will be fetched.

        Returns:
            Response object: json response with repository details.
    """
    repo = rpc.registry.get_repo(repo)
    if repo:
        return flask.jsonify(repo)

    return resource_not_found('repos', repo)


def update_downloads(repo):
    """ Function to update downloads for the given repository.

        Args:
            repo: required repository for which the details will be fetched.

        Returns:
            Response object: json response with repository details.
    """
    repo_url = parse.quote('/'.join([flask.url_for('repos'), repo]))

    try:
        rpc.registry.update_downloads(repo)
    except Exception as e:
        return resource_not_found('repos', repo)

    response = {
        'downloads': rpc.registry.get_repo(repo)['downloads'],
        'message': 'Repo({}) has been updated.'.format(repo),
        'repo_url': parse.quote('/'.join([flask.url_for('repos'), repo]))
    }
    return flask.jsonify(response)



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
