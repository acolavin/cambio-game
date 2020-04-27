#!/bin/env python
from . import create_app, socketio

app = create_app(debug=True)

if __name__ == '__main__':
    socketio.init_app(app, cors_allowed_origins='http://localhost:3000')

    from .main.routes import *

    socketio.run(app)
