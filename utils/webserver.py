from bottle import route, run, get, static_file


@get('/:path#.+#')
def server_static(path):
    return static_file(path, root=".")


# Serve favicon to avoid 404 logs
@get('/favicon.ico')
def get_favicon():
    return server_static('favicon.ico')


@route('/')
def index():
    return '<h1>INMETBot is online.</h1>'
