from enum import Enum
import numpy as np

CARD_SUITES = Enum('Suites', 'Club Spade Heart Diamond')
CARD_NUMBERS = Enum('Numbers', 'Ace 2 3 4 5 6 7 8 9 10 Jack Queen King')
SELF_PEAK_CARDS = [CARD_NUMBERS[_] for _ in ['7', '8']]
OTHER_PEAK_CARDS = [CARD_NUMBERS[_] for _ in ['9', '10']]
BLIND_SWAP_CARDS = [CARD_NUMBERS[_] for _ in ['Jack', 'Queen']]


class Card(object):
    _suit = None
    _value = None
    _id = None

    @property
    def suit(self):
        return self._suit

    @property
    def value(self):
        return self._value

    @property
    def id(self):
        return self._id

    def __init__(self, card_suite, card_number, card_id):
        self._suit = CARD_SUITES(card_suite)
        self._value = CARD_NUMBERS(card_number)
        self._id = card_id


def is_black_king(card):
    if card.value != CARD_NUMBERS['King']:
        return False
    if card.suit not in [CARD_SUITES['Club'], CARD_SUITES['Spade']]:
        return False
    return True


def generate_deck():
    random_cards = np.random.permutation(np.arange(52))
    random_suit = [card // 13 + 1 for card in random_cards]
    random_number = [card - 13 * (card // 13) + 1 for card in random_cards]
    return [Card(x, y, i) for x, y, i in zip(random_suit, random_number, range(len(random_suit)))]


class CambioGame(object):
    _deck = None
    _player_cards = None
    _player_order = None
    _active_player_card = None
    _active_player = None
    _cambio = None
    _discard = None
    _gameover = False
    _status = None

    @property
    def active_player(self):
        return self._active_player

    @property
    def player_cards(self):
        return self._player_cards

    @property
    def status(self):
        return self._status

    def __init__(self, player_ids):
        self._player_cards = {k: list() for k in player_ids}
        self._deck = generate_deck()
        self._discard = list()
        self._player_order = player_ids
        self._active_player = self._player_order[0]
        self._status = "initiated"

    def get_card_from_deck(self):
        if not len(self._deck):
            self._deck = [self._discard[i] for i in np.random.permutation(range(len(self._discard)))]
        return self._deck.pop()

    def deal(self):
        for _ in range(4):
            for player in self._player_cards:
                self._player_cards[player].append(self.get_card_from_deck())
        self._status = "started"

    def pregame_show(self):
        for player, cards in self._player_cards.items():
            for card_index in range(2):
                cards[card_index].show()

    def pregame_hide(self):
        for player, cards in self._player_cards.items():
            for card in cards:
                card.hide()

    def draw(self):
        assert self._active_player_card is None
        self._active_player_card = self.get_card_from_deck()
        self._active_player_card.show()

    def switch_self(self, card_index):
        existing_card = self._player_cards[self._active_player][card_index]
        self._player_cards[self._active_player][card_index] = self._active_player_card
        self._discard.append(existing_card)

    def discard(self):
        self._discard.append(self._active_player_card)

    def get_last_discarded(self):
        if self._discard is None or len(self._discard) == 0:
            return None
        else:
            return self._discard[-1]

    def peak_self(self, card_index):
        assert self._active_player_card.value in SELF_PEAK_CARDS
        card_of_interest = self._player_cards[self._active_player][card_index]
        card_of_interest.show()

    def peak_other(self, player_id, card_index):
        assert self._active_player_card.value in OTHER_PEAK_CARDS or is_black_king(self._active_player_card)
        self._player_cards[player_id][card_index].show()

    def blind_swap(self, other_player_id, self_card_index, other_card_index):
        active_card = self._active_player_card
        assert active_card.value in BLIND_SWAP_CARDS or is_black_king(active_card), "Invalid card!"
        assert self._cambio != other_player_id, "Player called cambio, you can't do that! "
        self_card = self._player_cards[self._active_player][self_card_index]
        other_card = self._player_cards[other_player_id][other_card_index]
        self._player_cards[self._active_player][self_card_index] = other_card
        self._player_cards[other_player_id][other_card_index] = self_card

    # operationally, the non-blind swap is actually a peak_other then a blind_swap with an action in-between.

    def call_cambio(self):
        self._cambio = self._active_player

    def end_turn(self):
        # hide the cards
        for player, cards in self._player_cards.items():
            for card in cards:
                card.hide()

        # revolve the next player:
        new_player_index = self._player_order.index(self._active_player) + 1
        if new_player_index == len(self._player_order):
            new_player_index = 0
        self._active_player = self._player_order[new_player_index]
        if self._active_player == self._cambio:
            self._active_player = None

        self._gameover = True








