import flask
from flask_socketio import SocketIO

socketio = SocketIO()


def create_app(debug=False):
    """Create an application."""
    app = flask.Flask(__name__)
    app.debug = debug
    app.config['SECRET_KEY'] = 'SECRET_KEY'

    socketio.init_app(app, logger=True)
    return app
