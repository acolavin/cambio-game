import hashlib
import random
from .game import CambioGame

HIDDEN_CARD = "HIDDEN"


class GameManager(object):
    _players = None
    _player2secret = None
    _secret2sid = None
    _secret2player = None
    _game = None

    @property
    def players(self):
        return self._players

    def get_player_secret(self, username):
        return self._player2secret[username]

    def get_player_username(self, user_token):
        if user_token in self._secret2player:
            return self._secret2player[user_token]
        raise GameError("Attempted to get game state for nonexistent player!")

    def username_taken(self, username):
        return username in self._players

    def add_player(self, username, sid):
        self._players.append(username)
        secret = hashlib.sha256((username + '%010i' % random.randint(0, 10**10)).encode('utf-8')).hexdigest()
        self._player2secret[username] = secret
        self._secret2player[secret] = username
        self._secret2sid[secret] = sid

    def get_game_state(self, requesting_user_token=None):

        requesting_user = self.get_player_username(requesting_user_token)

        if self._game is None:
            game_state = [{'name': user, 'cards': []} for user in self._players]
        else:
            game_state = [{'name': name,
                           'cards': [{'suite': HIDDEN_CARD, 'value': HIDDEN_CARD} for c in cards]
                           } for name, cards in self._game.player_cards.items() if name != requesting_user]
            game_state.append({'name': requesting_user,
                               'cards': [{'suite': c.suite.name,
                                          'value': c.value.name} for c in self._game.player_cards[requesting_user]]})
        return game_state

    def start_game(self):
        if self._game is None:
            self._game = CambioGame(self._players)
            self._game.deal()
        else:
            raise GameError("Game already started.")

    def __init__(self):
        self._players = list()
        self._player2secret = dict()
        self._secret2player = dict()
        self._secret2sid = dict()


class GameError(RuntimeError):
    """Runtime error in context of game.
    """
    pass