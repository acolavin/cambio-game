import hashlib
import random
from ..cambio.game import CambioGame
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
                                           **{'cards': [{'suit': HIDDEN_CARD,
                                                         'value': HIDDEN_CARD,
                                                         'id': c.id} for c in cards]}))

                else:
                    if game_stage == 'initial_card_preview':
                        hide_index = 2
                    elif game_stage == 'final_card_showcase':
                        hide_index = 4
                    else:
                        hide_index = 0

                    player_cards.append(dict(base_dict,
                                             **{'cards': [{'suit': c.suit.name if i < hide_index else HIDDEN_CARD,
                                                           'value': c.value.name if i < hide_index else HIDDEN_CARD,
                                                           'id': c.id} for i, c in enumerate(cards)]}))
        return {'game_state': player_cards,
                'last_discarded_card': self._game.get_last_discarded() if self._game is not None else None}

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