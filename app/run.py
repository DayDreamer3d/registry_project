import flask
from _impl.utils import convertors


app = flask.Flask(__name__)
app.url_map.converters['list'] = convertors.ListConverter


# TODO: @login_required decorator from Flask-Login
# cache to use redis


@app.route('/', methods=['GET', 'POST'])
def index():
    return 'Yeah !!'


@app.route('/api/tags')
def get_all_tags():
    return 'all tags'


@app.route('/api/repos')
def get_all_repos():
    return 'all repos'


@app.route('/api/repos/<list:tags>')
def get_repos_from_tags(tags):
    return ' . '.join(tags)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
