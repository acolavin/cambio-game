import flask
from flask_socketio import emit, join_room

from ..app import socketio, app
from ..cambio import gamemanager

rooms = dict()


@socketio.on('connect')
def sync():
    app.logger.info('global-connect: ' + str(flask.request.__dict__.keys()))


@socketio.on('start_game')
def start_game(data):
    room = rooms[data['roomid']]
    try:
        room.start_game()
        broadcast_new_state(data['roomid'])
    except gamemanager.GameError:
        emit('game_log', "Cannot start game. Game already started!")


def broadcast_new_state(roomid):
    room = rooms[roomid]
    for token, sid in room._secret2sid.items():
        emit('game_state',
             room.get_game_state(requesting_user_token=token), room=sid)


@socketio.on('propose_to_join')
def attempt_to_join_game(json):
    global rooms
    proposed_username = json['username']
    roomid = json['roomid']

    if roomid in rooms:
        if rooms[roomid].username_taken(proposed_username):
            emit('game_log', "Username %s taken in room %s!" % (proposed_username, roomid))
            return
    else:
        rooms[roomid] = gamemanager.GameManager()
    rooms[roomid].add_player(proposed_username, flask.request.sid)
    token = rooms[roomid].get_player_secret(proposed_username)
    app.logger.info("%s joined %s (%s)." % (proposed_username, roomid, flask.request.sid))
    emit('valid_username', {'token': token, 'roomid': roomid})


@socketio.on('joined_room')
def join_game(json):
    if 'roomid' in json and 'user_token' in json:
        if json['roomid'] in rooms:
            username = rooms[json['roomid']].get_player_username(json['user_token'])
            if username:
                join_room(json['roomid'])
                emit('token2username',
                     username)
                broadcast_new_state(json['roomid'])
                return

    emit('connection_unsuccessful', False)
