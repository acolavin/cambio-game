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
        app.logger.critical('Game is in an unrecognized stage! ({stage})'.format(stage=stage))
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


def broadcast_game_state(roomid, highlight=None):
    room = room_game_managers[roomid]
    for token, sid in room.secret2sid.items():
        payload = dict(room.get_game_state(requesting_user_token=token, highlight=highlight),
                       **{'room_and_token': {'roomid': roomid, 'user_token': token}})
        emit('game_state', payload, room=sid)
        if room.is_active_token(token):
            emit('update_active_card', room.game.active_player_card)


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
    emit('game_log', "{name} is ready.".format(name=room.get_player_username(data['user_token'])),
         room=data['roomid'])

    if room.all_players_ready():
        if room.get_game_stage() == 'initial_card_preview':
            update_button(data['roomid'],
                          active_player={'target': '',
                                         'text': '(draw a card!).',
                                         'disabled': True},
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
        emit('update_button', {'target': '', 'text': 'Ready.', 'disabled': 'True'})
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
        emit('game_log', "Click ""Continue Game"" when you're done looking at your cards!", room=data['roomid'])

    except gamemanager.GameError:
        emit('game_log', "Cannot start game. Game already started!")


@socketio.on('draw')
def draw_card(data):
    if not valid_data(data):
        return None

    room = room_game_managers[data['roomid']]
    if valid_move(room, 'draw_card', room.is_active_token(data['user_token'])):
        card = room.active_player_draw(data['user_token'])
        emit('update_active_card', card)
        emit('game_log', "{name} drew a card!".format(name=room.get_player_username(data['user_token'])),
             room=data['roomid'])


@socketio.on('discard_card')
def discard_card(data):
    if not valid_data(data):
        return None
    room = room_game_managers[data['roomid']]
    active_player = room.get_player_username(data['user_token'])
    if valid_move(room, 'discard_active_card', room.is_active_token(data['user_token'])) and room._reveal[active_player] is None:

        discard_id = room.active_player_discard(data['user_token'])

        emit('update_active_card', None)
        emit('game_log', "{name} discarded a card!".format(name=room.get_player_username(data['user_token'])),
             room=data['roomid'])
        broadcast_game_state(data['roomid'], highlight=discard_id)


@socketio.on("default_card_action")
def default_card_action(data):
    if not valid_data(data) or 'card_id' not in data:
        return None
    room = room_game_managers[data['roomid']]
    card_owner = room.get_card_ownership(data['card_id'])
    self_name = room.get_player_username(data['user_token'])
    if card_owner is None:
        return None
    elif valid_move(room, 'keep_active_card', room.is_active_token(data['user_token'])):

        if discard_id := room.keep_card(data['user_token'], data['card_id']):
            emit('update_active_card', None)
            emit('game_log', "{user} is keeping their drawn card. Good good good.".format(user=card_owner),
                 room=data['roomid'])
            broadcast_game_state(data['roomid'], highlight=[data['card_id'], discard_id])
    elif valid_move(room, 'attempt_discard_match', room.is_active_token(data['user_token'])):
        output2 = ""
        if self_name != card_owner:
            output1 = "{name1} attempted to discard {name2}'s card!".format(name1=self_name,
                                                                            name2=card_owner)
        else:
            output1 = "{name1} attempted to discard their own card!".format(name1=self_name,
                                                                            name2=card_owner)
        if (result := room.attempt_discard_match(data['user_token'], data['card_id'])) is not None:
            if result:
                if room.get_game_stage() == 'midgame_match_pause':
                    output2 = " Waiting for {name1} to give {name2} a card.".format(name1=self_name,
                                                                                    name2=card_owner)
                emit('game_log', output1 + "...Success!" + output2, room=data['roomid'])
                broadcast_game_state(data['roomid'], highlight=data['card_id'])
            elif result is None:
                pass
            else:
                emit('game_log', output1 + "...Failed!", room=data['roomid'])
                broadcast_game_state(data['roomid'], highlight=data['card_id'])
    elif valid_move(room, 'transfer_self_card', room.is_active_token(data['user_token'])):
        if room.give_card(data['user_token'], data['card_id']):
            broadcast_game_state(data['roomid'])


@socketio.on("secondary_card_action")
def secondary_card_action(data):
    if not valid_data(data) or 'card_id' not in data:
        return None
    room = room_game_managers[data['roomid']]
    card_owner = room.get_card_ownership(data['card_id'])
    self_name = room.get_player_username(data['user_token'])
    if valid_move(room, 'peek_self_card', room.is_active_token(data['user_token'])):
        if handle_78(room, self_name, data['card_id'], card_owner) is not None:
            broadcast_game_state(data['roomid'], highlight=[data['card_id']])
    return


def handle_78(room, self_name, data_card_id, card_owner):
    if self_name != card_owner:
        return None
    return room.toggle_reveal_card(self_name, data_card_id)