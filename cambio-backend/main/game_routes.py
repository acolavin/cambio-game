from flask_socketio import emit, join_room
import datetime
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

    update_button(roomid,
                  active_player={'target': 'call_cambio',
                                 'text': 'CAMBIO!',
                                 'disabled': False},
                  inactive_player={'target': '',
                                   'text': 'CAMBIO!',
                                   'disabled': True})
    if room.gameover():
        emit('game_log', "!!GAME OVER!!! Melissa wins. TODO: Don't hard code this in...", room=roomid)


def valid_data(data, limiting=True):
    if not all([k in data for k in ['roomid', 'user_token']]):
        return False
    if data['roomid'] not in room_game_managers:
        return False
    if data['user_token'] not in room_game_managers[data['roomid']].secret2sid:
        return False

    room = room_game_managers[data['roomid']]
    if (datetime.datetime.now() - room.last_action).total_seconds() < 0.2 and limiting:
        return False

    room.last_action = datetime.datetime.now()

    return True


@socketio.on('ready')
def user_is_ready(data):
    if not valid_data(data, limiting=False):
        return None
    app.logger.info(data)
    room = room_game_managers[data['roomid']]
    room.mark_player_as_ready(data['user_token'])
    emit('game_log', "{name} is ready.".format(name=room.get_player_username(data['user_token'])),
         room=data['roomid'])

    if room.all_players_ready():
        if room.get_game_stage() == 'initial_card_preview':
            update_button(data['roomid'],
                          active_player={'target': 'call_cambio',
                                         'text': 'CAMBIO!',
                                         'disabled': False},
                          inactive_player={'target': '',
                                           'text': 'CAMBIO!',
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
    if not valid_data(json, limiting=False):
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
    if not valid_data(data, limiting=False):
        return False
    gm = room_game_managers[data['roomid']]
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
    if valid_move(room, 'discard_active_card', room.is_active_token(data['user_token'])):

        discard_id = room.active_player_discard_and_end_turn(data['user_token'])

        emit('update_active_card', None)
        emit('game_log', "{name} discarded a card!".format(name=room.get_player_username(data['user_token'])),
             room=data['roomid'])
        broadcast_game_state(data['roomid'], highlight=discard_id)


@socketio.on("default_card_action")
def default_card_action(data):

    if not valid_data(data) or 'card_id' not in data:
        app.logger.info('No appropriate default action')
        return None
    room = room_game_managers[data['roomid']]
    app.logger.info('Default action for card ' + str(data['card_id']) + ' room state ' + room.get_game_stage())
    card_owner = room.get_card_ownership(data['card_id'])
    self_name = room.get_player_username(data['user_token'])
    if card_owner is None or room.gameover():
        return None
    elif valid_move(room, 'keep_active_card', room.is_active_token(data['user_token'])):
        active_card_id = room.game._active_player_card.id
        if discard_id := room.keep_card(data['user_token'], data['card_id']):
            emit('update_active_card', None)
            emit('game_log', "{user} is keeping their drawn card. Good good good.".format(user=card_owner),
                 room=data['roomid'])
            broadcast_game_state(data['roomid'], highlight=[data['card_id'], discard_id,
                                                            active_card_id])
    elif valid_move(room, 'attempt_discard_match', room.is_active_token(data['user_token'])):
        output2 = ""

        if self_name != card_owner:
            output1 = "{name1} attempted to discard {name2}'s card!".format(name1=self_name,
                                                                            name2=card_owner)
        else:
            output1 = "{name1} attempted to discard their own card!".format(name1=self_name,
                                                                            name2=card_owner)

        if room.last_card_match == room.game.get_last_discarded():
            emit('game_log', output1 + "...Failed ! Only one match allowed at a time!", room=data['roomid'])
            broadcast_game_state(data['roomid'], highlight=data['card_id'])
        elif (result := room.attempt_discard_match(data['user_token'], data['card_id'])) is not None:
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
    else:
        app.logger.error("Unhandled default card action.")


@socketio.on("secondary_card_action")
def secondary_card_action(data):

    if not valid_data(data) or 'card_id' not in data:
        app.logger.info('No appropriate secondary action')
        return None

    roomid = data['roomid']
    room = room_game_managers[roomid]
    app.logger.info('Secondary action for card ' + str(data['card_id']) + ' room state ' + room.get_game_stage())
    card_owner = room.get_card_ownership(data['card_id'])
    self_name = room.get_player_username(data['user_token'])
    if data['card_id'] is None or room.gameover():
        return None

    if valid_move(room, 'peek_self_card', room.is_active_token(data['user_token'])):
        app.logger.info('Attempt peak self card')
        if handle_78(room, self_name, data['card_id'], card_owner):
            emit('game_log', f"{self_name} is peaking at their own card!", room=roomid)
            room.set_game_stage('midgame_player_postreveal_78910')
            broadcast_game_state(roomid, highlight=[data['card_id']])
    if valid_move(room, 'peek_other_card', room.is_active_token(data['user_token'])):
        if handle_910(room, self_name, data['card_id'], card_owner):
            emit('game_log', f"{self_name} is peaking at {card_owner}'s card!", room=roomid)
            room.set_game_stage('midgame_player_postreveal_78910')
            broadcast_game_state(roomid, highlight=[data['card_id']])
    if valid_move(room, 'switch_self_other_card', room.is_active_token(data['user_token'])):
        if (to_highlight := handle_jqk(room, self_name, data['card_id'], card_owner)):

            emit('game_log', f"{self_name} is switching cards!", room=roomid)
            broadcast_game_state(roomid, highlight=to_highlight)
            if len(to_highlight) == 2:
                emit('update_active_card', None)
    return


def handle_78(room, self_name, data_card_id, card_owner):
    if self_name != card_owner or data_card_id is None:
        return None

    return room.toggle_reveal_card(self_name, data_card_id)


def handle_910(room, self_name, data_card_id, card_owner):
    if self_name == card_owner or data_card_id is None:
        return None

    return room.toggle_reveal_card(self_name, data_card_id)


def handle_jqk(room, self_name, data_card_id, card_owner):
    """

    Parameters
    ----------
    room : gamemanager.GameManager
    self_name
    data_card_id
    card_owner

    Returns
    -------

    """

    if self_name == card_owner:
        done = room.select_and_switch_propose_self_card(self_name, data_card_id)
    else:
        done = room.select_and_switch_propose_other_card(self_name, data_card_id)
    return [_ for _ in done if _ is not None]


@socketio.on("call_cambio")
def call_cambio(data):
    if not valid_data(data):
        app.logger.info('No appropriate secondary action')
        return None

    roomid = data['roomid']
    room = room_game_managers[roomid]
    app.logger.info('Calling cambio!')
    success = room.call_cambio(data['user_token'])
    if success:
        broadcast_game_state(roomid)
        self_name = room.get_player_username(data['user_token'])
        emit('game_log', f"{self_name} is switching cards!", room=roomid)
        emit('update_active_card', None)
