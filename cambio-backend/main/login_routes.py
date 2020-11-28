import flask
from flask_socketio import emit

from ..app import socketio, app, room_game_managers
from .gamemanager import GameManager


VALID_CHARACTERS = 'abcdefghijklmnopqrstuvwxyz-_0123456789'


@socketio.on('connect')
def sync():
    app.logger.info('New user connected. ' + str(flask.request.sid))


@socketio.on('propose_to_join')
def attempt_to_join_game(json):
    proposed_username = str(json['username']).lower()
    roomid = str(json['roomid']).lower()

    for key, val in zip(['username', 'room'], [proposed_username, roomid]):
        if not all([_ in VALID_CHARACTERS for _ in val]) or len(val) < 2 or len(val) > 20:
            emit('game_log', "{val} is an invalid {key}!".format(val=val, key=key))
            return

    if roomid in room_game_managers:
        if room_game_managers[roomid].username_taken(proposed_username):
            emit('game_log', "Username %s taken in room %s!" % (proposed_username, roomid))
            return
        elif room_game_managers[roomid].game is not None:
            emit('game_log', "Game in room %s has already started!" % (roomid))
            return
    else:
        room_game_managers[roomid] = GameManager()
    token = room_game_managers[roomid].add_player(proposed_username, flask.request.sid)
    app.logger.info("%s joined %s (%s)." % (proposed_username, roomid, flask.request.sid))
    emit('enter_room', {'token': token, 'roomid': roomid})


