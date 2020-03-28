#
# Copyright (C) Florian Denis - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited.
# Proprietary and confidential.
#

import logging
import random

from enum import Enum

from . import constants


log = logging.getLogger(__name__)


"""
Full game context holding the state of the current game for the server side
Contains all the logic to advance the game to next level
"""
class Game:

    State = Enum('State', [(a, a) for a in (
        'WAITING_FOR_PLAYERS',
        'READY_TO_START',
        'ONGOING'
    )], type=str)


    def __init__(self):
        # Local context
        self._players = []
        self._cards = []
        self._hands = {}
        self._starting_player = 0

        self._round_ongoing = False

        # Callback
        self.on_status_changed = None


    @property
    def state(self):
        if len(self._players) < 4:
            return Game.State.WAITING_FOR_PLAYERS
        if not self._round_ongoing:
            return Game.State.READY_TO_START
        return Game.State.ONGOING


    @property
    def round_ordered_players(self):
        return [self._players[idx % 4] for idx in range(
            self._starting_player, self._starting_player + 4)]


    @property
    def card_deck(self):
        # TODO: This should be tracked from one game to the other,
        # not randomized at each new round
        all_cards = [card.value for card in constants.Card]
        random.shuffle(all_cards)
        return all_cards


    def _deal(self, deck):

        ordered_players = self.round_ordered_players

        idx = 0
        dealt = {}

        # 3
        for i in range(4):
            dealt[ordered_players[i]] = deck[idx:idx+3]
            idx += 3

        # 2
        for i in range(4):
            dealt[ordered_players[i]] += deck[idx:idx+2]
            idx += 2

        # 3
        for i in range(4):
            dealt[ordered_players[i]] += deck[idx:idx+3]
            idx += 3

        return dealt


    def start_round(self):
        if self.state != Game.State.READY_TO_START:
            log.error("Invalid state to start new round")
            return

        self._round_ongoing = True
        self._cards = []

        self._hands = self._deal(self.card_deck)

        self.on_status_changed()


    def _reset_round(self):
        self._cards = []
        self._hands = {}
        self._starting_player = (self._starting_player+ 1) % 4
        self._round_ongoing = False

        self.on_status_changed()


    def add_player(self, player):
        if self.state != Game.State.WAITING_FOR_PLAYERS:
            log.error("Attempting to add player to already full game")
            return

        self._players.append(player)

        if self.state is Game.State.READY_TO_START:
            self.start_round()
        else:
            self.on_status_changed()


    def remove_player(self, player):
        if not player in self._players:
            log.error("Attempting to add player to already full game")
            return

        self._players.remove(player)

        if self.state == Game.State.ONGOING:
            log.info("Player left while in a round: resetting")
            _reset_round()
        else:
            self.on_status_changed()


    def proxy_for_player(self, player):
        if not player in self._players:
            log.error("Attempting to generate a proxy for a player not in game")
            return None

        # Create a permutation so that the requesting player is always index 0
        player_index = self._players.index(player)
        idx_permutation = [
            (player_index + 0) % 4,
            (player_index + 1) % 4,
            (player_index + 2) % 4,
            (player_index + 3) % 4
        ]


        proxy = GameProxy()

        proxy._state = self.state

        proxy._players = [
            self._players[idx].name if idx < len(self._players) else ""
                for idx in idx_permutation
        ]

        proxy._cards = [
            self._cards[idx] if idx < len(self._cards) else ""
                for idx in idx_permutation
        ]

        proxy._hand = self._hands[player] if player in self._hands else []
        # Sort by order
        all_cards = [card.value for card in constants.Card] + ['']
        proxy._hand.sort(key=lambda x: all_cards.index(x))


        proxy._starting_player = self._starting_player

        return proxy


"""
A simplified game context containing only what is necessary for the client side,
and not game logic
"""
class GameProxy:

    def __init__(self):
        self._state = None
        self._starting_player = 0
        self._players = []
        self._cards = []
        self._hand = []


    @property
    def state(self):
        return self._state


    @property
    def players(self):
        return self._players


    @property
    def hand(self):
        return self._hand



    def to_args(self):
        args = []

        args.append(self._state)
        args.append(str(self._starting_player))

        args += self._players
        args += self._cards

        args.append(str(len(self._hand)))
        args += self._hand


        return args


def from_args(args):

    proxy = GameProxy()

    idx = 0

    proxy._state = args[idx]
    idx += 1

    proxy._starting_player = int(args[idx])
    idx += 1

    proxy._players = args[idx: idx+4]
    idx += 4

    proxy._cards = args[idx: idx+4]
    idx += 4

    hand_count = int(args[idx])
    idx += 1
    proxy._hand = args[idx: idx+hand_count]
    idx += hand_count

    return proxy
