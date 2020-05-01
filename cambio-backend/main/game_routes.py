from flask_socketio import emit, join_room
from ..app import socketio, app, room_game_managers
from . import gamemanager
from . import GAME_RULES


def valid_move(gm, move, active):
    """

    Parameters
    ----------
    gm : gamemanager.GameManager
    move : str
    active : bool

    Returns
    -------

    """
    stage = gm.get_game_stage()
    if stage not in GAME_RULES:
        app.logger.critical('Game is in an unrecognized state!')
        return False
    if GAME_RULES[stage]['type'] == 'global':
        if move in GAME_RULES[stage]['allowed_actions']:
            return True
    elif GAME_RULES[stage]['type'] == 'player':
        if active:
            return move in GAME_RULES[stage]['active_allowed_actions']
        else:
            return move in GAME_RULES[stage]['inactive_allowed_actions']

    return False


def broadcast_game_state(roomid, action=None):
    room = room_game_managers[roomid]
    game_stage = room.get_game_stage()

    for token, sid in room.secret2sid.items():

        emit('game_state',
             dict(room.get_game_state(requesting_user_token=token),
                  **{'room_and_token': {'roomid': roomid, 'user_token': token}}),
             room=sid)


def valid_data(data):
    if not all([k in data for k in ['roomid', 'user_token']]):
        return False
    if data['roomid'] not in room_game_managers:
        return False
    if data['user_token'] not in room_game_managers[data['roomid']].secret2sid:
        return False
    return True


@socketio.on('ready')
def user_is_ready(data):
    if not valid_data(data):
        return None
    app.logger.info(data)
    room = room_game_managers[data['roomid']]
    room.mark_player_as_ready(data['user_token'])

    if room.all_players_ready():
        if room.get_game_stage() == 'initial_card_preview':
            update_button(data['roomid'],
                          active_player={'target': 'draw',
                                         'text': 'Draw.',
                                         'disabled': False},
                          inactive_player={'target': '',
                                         'text': '(no action available).',
                                         'disabled': True})

            room.set_game_stage('midgame_predraw')
            broadcast_game_state(data['roomid'])
            return
        elif room.get_game_stage() == 'pre_game':
            payload = {'target': 'start_game',
                       'text': 'Start the game!',
                       'disabled': False}
            update_button(data['roomid'], active_player=payload, inactive_player=payload)
        else:
            raise NotImplementedError()


    else:
        emit('update_button', {'target':'', 'text':'Waiting for others...', 'disabled':'True'})
        return


def update_button(roomid, active_player=None, inactive_player=None):
    room = room_game_managers[roomid]
    for token, sid in room.secret2sid.items():
        if room.is_active_token(token) and active_player is not None:
            emit('update_button', active_player, room=room.secret2sid[token])
        elif not room.is_active_token(token) and inactive_player is not None:
            emit('update_button', inactive_player, room=room.secret2sid[token])


@socketio.on('joined_room')
def join_game(json):
    if not valid_data(json):
        app.logger.info(json)
        app.logger.critical("Attempt to join game with invalid data!")
        return False
    room = room_game_managers[json['roomid']]
    username = room.get_player_username(json['user_token'])
    if username:
        join_room(json['roomid'])
        emit('token2username',
             username)
        room.reset_ready()
        broadcast_game_state(json['roomid'])
        update_button(json['roomid'], inactive_player={'target': 'ready',
                                                       'text': 'Ready.',
                                                       'disabled': False})
        emit('game_log', "Click ""Ready"" when you're ready!")
        return

    emit('connection_unsuccessful', False)


@socketio.on('start_game')
def start_game(data):
    if not valid_data(data):
        return False
    gm = room_game_managers[data['roomid']]
    app.logger.info(gm.get_game_stage())
    if not valid_move(gm, 'start_game', gm.is_active_token(data['user_token'])):
        app.logger.info('Attempt to start game at invalid stage!')
        return None
    elif len(gm.players) < 2:
        emit('game_log', "Need at least two players!")
        return None
    try:
        gm.start_game()
        gm.reset_ready()
        broadcast_game_state(data['roomid'])
        ready_button = {'target': 'ready',
                        'text': 'Continue Game',
                        'disabled': False}
        update_button(data['roomid'],
                      active_player=ready_button,
                      inactive_player=ready_button)
        emit('game_log', "Click ""Continue Game"" when you're done looking at your cards!")

    except gamemanager.GameError:
        emit('game_log', "Cannot start game. Game already started!")

