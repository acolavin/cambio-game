#!/bin/env python
from . import create_app, socketio

app = create_app(debug=True)

room_game_managers = dict()  # BEHOLD! All the game stage data goes into this dictionary. Scary!

if __name__ == '__main__':
    socketio.init_app(app, cors_allowed_origins='http://localhost:3000')

    from .main.login_routes import *

    socketio.run(app)