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
    game = None
    _ready = None


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
        return self.game.active_player if self.game is not None else None

    def is_active_token(self, token):
        return self.get_active_player() == self.secret2player[token]

    def get_game_stage(self):
        if self.game is None:
            return 'pre_game'
        else:
            return self.game.stage

    def set_game_stage(self, stage):
        self.game.stage = stage

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

    def get_game_state(self, requesting_user_token, highlight=None):

        requesting_user = self.get_player_username(requesting_user_token)
        active_user = self.game.active_player if self.game is not None else None
        game_stage = self.get_game_stage()
        app.logger.info("Active Player: " + str(active_user))
        if self.game is None:
            player_cards = [{'name': user,
                             'cards': [],
                             'active_user': False,
                             'is_self': requesting_user == user} for user in self._players]
        else:
            player_cards = []
            for name, cards in self.game.player_cards.items():
                base_dict = {'name': name,
                             'is_self': requesting_user == name,
                             'active_user': name == active_user}
                if name != requesting_user:
                    player_cards.append(dict(base_dict,
                                           **{'cards': [serialize_card(c,
                                                                       hide=True,
                                                                       highlight=GameManager.cardmatch(c, highlight)) for c in cards]}))

                else:
                    if game_stage == 'initial_card_preview':
                        hide_index = 2
                    elif game_stage == 'final_card_showcase':
                        hide_index = 4
                    else:
                        hide_index = 0

                    player_cards.append(dict(base_dict,
                                             **{'cards': [serialize_card(c,
                                                                         hide=i >= hide_index,
                                                                         highlight=GameManager.cardmatch(c, highlight)) for i, c in enumerate(cards)]}))
        return {'game_state': player_cards,
                'last_discarded_card': serialize_card(self.game.get_last_discarded(),
                                                      hide=False,
                                                      highlight=GameManager.cardmatch(self.game.get_last_discarded(),
                                                                                      highlight)) if self.game is not None else None}

    def start_game(self):
        if self.game is None:
            self.game = CambioGame(self._players)
            self.game.deal()
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
            self.game.draw()

        active_card = self.game.active_player_card
        action, action_string = '', '(this card has no power)'

        if active_card.value in SELF_PEAK_CARDS:
            action = 'self_peak'
            action_string = 'Click to activate power.'
            self.set_game_stage('midgame_player_postdraw_78')
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
        return dict(serialize_card(active_card, hide=False, highlight=True),
                    **{'action': action, 'action_string': action_string})

    def active_player_discard(self, token):
        if self.is_active_token(token):
            self.game.discard_active_card()
            self.game.end_turn()
            self.set_game_stage('midgame_predraw')
            return self.game.get_last_discarded().id
        return

    def get_card_ownership(self, card_id):
        for player, cards in self.game.player_cards.items():
            if any([GameManager.cardmatch(c, card_id) for c in cards]):
                return player
        return None

    def get_card(self, card_id):
        if card_id in self.game._card_id_registry:
            return self.game._card_id_registry[card_id]
        return None

    @staticmethod
    def cardmatch(_c, _id):
        if _c is None:
            return False
        if isinstance(_id, list):
            return _c.id in _id
        else:
            return _c.id == _id

    def attempt_discard_match(self, token, id):
        previous_stage = self.get_game_stage()
        self.set_game_stage('midgame_match_pause')
        if previous_stage == 'midgame_match_pause':
            return None
        attempter = self.get_player_username(token)
        # This should go into game object
        if (last_discard := self.game.get_last_discarded()) is not None:
            if last_discard.value == self.get_card(id).value:
                card_owner = self.get_card_ownership(id)
                if self.game._cambio != card_owner:
                    self.game._discard.append(self.get_card(id))
                    self.game._player_cards[card_owner] = [c if not GameManager.cardmatch(c, id) else None for c in self.game._player_cards[card_owner]]
                    if attempter == card_owner:
                        self.set_game_stage(previous_stage)
                    elif len(self.game._player_cards[attempter]) == 0:
                        self.set_game_stage(previous_stage)
                    else:
                        self.game._switchcard_player = (attempter, card_owner, previous_stage)
                    return True
            else:
                self.game._player_cards[attempter].append(self.game.get_card_from_deck())
                self.set_game_stage(previous_stage)
                return False
        self.set_game_stage(previous_stage)
        return None

    def give_card(self, token, id):
        attempter = self.get_player_username(token)
        card_owner = self.get_card_ownership(id)
        if self.game._switchcard_player is None:
            return False
        elif attempter != card_owner or attempter != self.game._switchcard_player[0]:
            return False
        self.game._player_cards[self.game._switchcard_player[1]].extend(
            [c for c in self.game._player_cards[card_owner] if GameManager.cardmatch(c, id)])

        self.game._player_cards[card_owner] = [c if not GameManager.cardmatch(c, id) else None for c in
                                               self.game._player_cards[card_owner]]

        self.set_game_stage(self.game._switchcard_player[2])
        self.game._switchcard_player = None

        return True

    def keep_card(self, token, id):
        active_user = self.get_active_player()
        if not self.is_active_token(token):
            return False
        elif id not in [c.id for c in self.game.player_cards[active_user]]:
            return False
        if self.game._active_player_card is not None:
            old_card = [c for c in self.game.player_cards[active_user] if c.id == id][0]
            self.game.player_cards[active_user] = [c if c.id != id else self.game._active_player_card for c in self.game.player_cards[active_user]]
            self.game._active_player_card = old_card
            return self.active_player_discard(token)

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


def serialize_card(card, hide, highlight):
    if card is None:
        return {'suit': '', 'value': '', 'id': '', 'highlight': highlight}
    if hide:
        return {'suit': HIDDEN_CARD,
                'value': HIDDEN_CARD,
                'id': card.id,
                'highlight': highlight}
    else:
        return {'suit': card.suit.name,
                'value': card.value.name,
                'id': card.id,
                'highlight': highlight}
