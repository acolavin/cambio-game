import hashlib
import random
from ..cambio.game import CambioGame, SELF_PEAK_CARDS, OTHER_PEAK_CARDS, BLIND_SWAP_CARDS, is_black_king
from ..app import app

HIDDEN_CARD = "HIDDEN"


class GameManager(object):
    _players = None
    _player2secret = None
    _secret2sid = None
    _secret2player = None
    _game = None
    _ready = None
    _state = None


    @property
    def players(self):
        return self._players

    @property
    def secret2sid(self):
        return self._secret2sid if self._secret2sid is not None else None

    @property
    def secret2player(self):
        return self._secret2player if self._secret2player is not None else None

    def get_active_player(self):
        return self._game.active_player if self._game is not None else None

    def is_active_token(self, token):
        return self.get_active_player() == self.secret2player[token]

    def get_game_stage(self):
        if self._game is None:
            return 'pre_game'
        else:
            return self._game.stage

    def set_game_stage(self, stage):
        self._game.stage = stage

    def get_player_secret(self, username):
        return self._player2secret[username]

    def get_player_username(self, user_token):
        if user_token in self._secret2player:
            return self._secret2player[user_token]
        raise GameError("Attempted to get game stage for nonexistent player!")

    def username_taken(self, username):
        return username in self._players

    def add_player(self, username, sid):
        self._players.append(username)
        secret = hashlib.sha256((username + '%010i' % random.randint(0, 10**10)).encode('utf-8')).hexdigest()
        self._player2secret[username] = secret
        self._secret2player[secret] = username
        self._secret2sid[secret] = sid
        self._ready[username] = False
        return secret

    def get_game_state(self, requesting_user_token=None):

        requesting_user = self.get_player_username(requesting_user_token)
        active_user = self._game.active_player if self._game is not None else None
        game_stage = self.get_game_stage()
        app.logger.info("Active Player: " + str(active_user))
        if self._game is None:
            player_cards = [{'name': user,
                             'cards': [],
                             'active_user': False,
                             'is_self': requesting_user == user} for user in self._players]
        else:
            player_cards = []
            for name, cards in self._game.player_cards.items():
                base_dict = {'name': name,
                             'is_self': requesting_user == name,
                             'active_user': name == active_user}
                if name != requesting_user:
                    player_cards.append(dict(base_dict,
                                           **{'cards': [serialize_card(c, hide=True) for c in cards]}))

                else:
                    if game_stage == 'initial_card_preview':
                        hide_index = 2
                    elif game_stage == 'final_card_showcase':
                        hide_index = 4
                    else:
                        hide_index = 0

                    player_cards.append(dict(base_dict,
                                             **{'cards': [serialize_card(c, hide=i >= hide_index) for i, c in enumerate(cards)]}))
        return {'game_state': player_cards,
                'last_discarded_card': serialize_card(self._game.get_last_discarded(),
                                                      hide=False) if self._game is not None else None}

    def start_game(self):
        if self._game is None:
            self._game = CambioGame(self._players)
            self._game.deal()
        else:
            raise GameError("Game already started.")

    def mark_player_as_ready(self, token):
        self._ready[self.get_player_username(token)] = True

    def reset_ready(self):
        self._ready = {k: False for k in self._players}

    def all_players_ready(self):
        app.logger.info(self._ready)
        return all(self._ready.values())

    def active_player_draw(self, token):
        if self.is_active_token(token):
            self._game.draw()

        active_card = self._game.active_player_card
        action, action_string = '', '(this card has no power)'

        if active_card.value in SELF_PEAK_CARDS:
            action = 'self_peak'
            action_string = 'Click to activate power.'
            self.set_game_stage('midgame_player_postdraw_78')
            self.set_game_stage('')
        elif active_card.value in OTHER_PEAK_CARDS:
            action = 'other_peak'
            action_string = 'Click to activate power.'
            self.set_game_stage('midgame_player_postdraw_910')
        elif active_card.value in BLIND_SWAP_CARDS:
            action = 'blind_swap'
            action_string = 'Click to activate power.'
            self.set_game_stage('midgame_player_postdraw_jq')
        elif is_black_king(active_card):
            action = 'nonblind_swap'
            action_string = 'Click to activate power.'
            self.set_game_stage('midgame_active_player_postdraw_blackking')
        else:
            self.set_game_stage('midgame_postdraw_nopower')
            pass
        return dict(serialize_card(active_card, hide=False),
                    **{'action': action, 'action_string': action_string})

    def active_player_discard(self, token):
        if self.is_active_token(token):
            self._game.discard()
            self._game.end_turn()
            self.set_game_stage('midgame_predraw')

        return

    def __init__(self):
        self._players = list()
        self._player2secret = dict()
        self._secret2player = dict()
        self._secret2sid = dict()
        self._ready = dict()


class GameError(RuntimeError):
    """Runtime error in context of game.
    """
    pass


def serialize_card(card, hide):
    if card is None:
        return {'suit': '', 'value': '', 'id': ''}
    if hide:
        return {'suit': HIDDEN_CARD,
                'value': HIDDEN_CARD,
                'id': card.id}
    else:
        return {'suit': card.suit.name,
                'value': card.value.name,
                'id': card.id}
