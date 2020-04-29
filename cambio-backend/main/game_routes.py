from flask_socketio import emit, join_room
from ..app import socketio, app, rooms
from ..cambio import gamemanager


@socketio.on('start_game')
def start_game(data):
    room = rooms[data['roomid']]
    try:
        room.start_game()
        broadcast_game_state(data['roomid'])

    except gamemanager.GameError:
        emit('game_log', "Cannot start game. Game already started!")


def broadcast_game_state(roomid):
    room = rooms[roomid]
    for token, sid in room._secret2sid.items():
        emit('game_state',
             dict(room.get_game_state(requesting_user_token=token),
             **{'room_and_token': {'roomid': roomid, 'token': token}}), room=sid)


@socketio.on('ready')
def user_is_ready(data):
    app.logger.info(data)
    room = rooms[data['roomid']]
    room.mark_player_as_ready(data['token'])
    if room.all_players_ready():
        payload = {'target': 'start_game',
                   'text': 'Start the game!',
                   'disabled': False}
        emit('update_button', payload, room=data['roomid'])
    else:
        payload = {'target': '',
                   'text': 'Waiting for others...',
                   'disabled': True}
        emit('update_button', payload)


@socketio.on('joined_room')
def join_game(json):
    if 'roomid' in json and 'user_token' in json:
        if json['roomid'] in rooms:
            username = rooms[json['roomid']].get_player_username(json['user_token'])
            if username:
                join_room(json['roomid'])
                emit('token2username',
                     username)
                broadcast_game_state(json['roomid'])
                return

    emit('connection_unsuccessful', False)
