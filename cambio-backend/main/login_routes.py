import flask
from flask_socketio import emit

from ..app import socketio, app, rooms
from ..cambio.gamemanager import GameManager


@socketio.on('connect')
def sync():
    app.logger.info('New user connected. ' + str(flask.request.sid))


@socketio.on('propose_to_join')
def attempt_to_join_game(json):
    proposed_username = json['username']
    roomid = json['roomid']
    # TODO: validate username
    if roomid in rooms:
        if rooms[roomid].username_taken(proposed_username):
            emit('game_log', "Username %s taken in room %s!" % (proposed_username, roomid))
            return
    else:
        rooms[roomid] = GameManager()
    token = rooms[roomid].add_player(proposed_username, flask.request.sid)
    app.logger.info("%s joined %s (%s)." % (proposed_username, roomid, flask.request.sid))
    emit('valid_username', {'token': token, 'roomid': roomid})


