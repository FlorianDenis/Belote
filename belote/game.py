#
# Copyright (C) Florian Denis - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited.
# Proprietary and confidential.
#

import logging
import random
import threading

from enum import Enum

from . import card
from . import constants
from . import player


log = logging.getLogger(__name__)


"""
Full game context holding the state of the current game for the server side
Contains all the logic to advance the game to next level
"""
class Game:

    State = Enum('State', [(a, a) for a in (
        'WAITING_FOR_PLAYERS',
        'READY_TO_START',
        'ANNOUNCING',
        'ONGOING'
    )], type=str)


    def __init__(self):
        # Local context
        self._players = []
        self._cards = {}
        self._hands = {}
        self._starting_player_round = 0
        self._starting_player_pli = 0

        self._trump_suit = None
        self._round_ongoing = False

        # Callback
        self.on_status_changed = None


    @property
    def state(self):
        if len(self._players) < 4:
            return Game.State.WAITING_FOR_PLAYERS
        if not self._round_ongoing:
            return Game.State.READY_TO_START
        if self._trump_suit == None:
            return Game.State.ANNOUNCING
        return Game.State.ONGOING


    @property
    def card_deck(self):
        # TODO: This should be tracked from one game to the other,
        # not randomized at each new round
        all_cards = card.all
        random.shuffle(all_cards)
        return all_cards


    def _deal(self, deck):

        ordered_players = [self._players[idx % 4] for idx in range(
            self._starting_player_round, self._starting_player_round + 4)]

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


    def _start_round(self):
        if self.state != Game.State.READY_TO_START:
            log.error("Invalid state to start new round")
            return

        self._round_ongoing = True
        self._hands = self._deal(self.card_deck)

        self.on_status_changed()


    def set_player_ready(self, player):
        if self.state != Game.State.READY_TO_START:
            log.error("Attempting to set player ready while in invalid state")
            return

        if not player in self._players:
            log.error("Attempting to set ready unknown player")
            return

        player.set_ready(True)

        for player in self._players:
            if not player.is_ready:
                self.on_status_changed()
                return

        # Everyone ready: let's go
        self._start_round()



    def pick_trump(self, player, suit):
        if self.state != Game.State.ANNOUNCING:
            log.error("Can only pick the trump suit while announcing")
            return

        if not player is self._players[self._starting_player_round]:
            log.error("Only the starting player shall select the trump suit")
            return

        self._trump_suit = suit
        self.on_status_changed()


    def play_card(self, player, card):
        if self.state != Game.State.ONGOING:
            log.error("Invalid state to play card")
            return

        current_player_idx = (self._starting_player_pli + len(self._cards)) % 4
        if player is not self._players[current_player_idx]:
            log.error("Not player's turn")
            return

        hand = self._hands[player]
        if not card in hand:
            log.error("Trying to play card not in player's hand")
            return

        if player in self._cards:
            log.error("Player already played")
            return

        self._hands[player].remove(card)
        self._cards[player] = card

        if len(self._cards) == 4 and len(self._hands[player]) == 0:
            # Round completed, will terminate the round in 2 seconds
            threading.Timer(2, self._finish_round).start()

        elif len(self._cards) == 4:
            # Hand completed, will reset the pli in 2 seconds
            threading.Timer(2, self._finish_pli).start()

        self.on_status_changed()


    def _finish_pli(self):

        # Find out who won it
        ordered_players = [self._players[idx % 4] for idx in range(
            self._starting_player_pli, self._starting_player_pli + 4)]




        self._cards = {}

        # TODO: Not the next one, but the one who got the previous round
        self._starting_player_pli = (self._starting_player_pli + 1) % 4

        self.on_status_changed()



    def _reset_round(self):
        self._cards = {}
        self._hands = {}
        self._starting_player_round = (self._starting_player_round + 1) % 4
        self._starting_player_pli = self._starting_player_round
        self._round_ongoing = False
        self._trump_suit = None

        for player in self._players:
            player.set_ready(False)

        self.on_status_changed()


    def _finish_round(self):
        # TODO: count points, display them, cut deck for next
        self._reset_round()


    def add_player(self, player):
        if self.state != Game.State.WAITING_FOR_PLAYERS:
            log.error("Attempting to add player to already full game")
            return

        self._players.append(player)

        self.on_status_changed()


    def remove_player(self, player):
        if not player in self._players:
            log.error("Attempting to remove unknown player")
            return

        state = self.state
        self._players.remove(player)

        if self._round_ongoing:
            log.info("Player left while in a round: resetting")
            self._reset_round()
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
        proxy._trump_suit = self._trump_suit

        proxy._players = [
            self._players[idx].name if idx < len(self._players) else ""
                for idx in idx_permutation
        ]

        proxy._cards = [
            self._cards[self._players[idx]]
                if idx < len(self._players) and self._players[idx] in self._cards
                    else card.Card("")
                for idx in idx_permutation
        ]

        proxy._hand = self._hands[player] if player in self._hands else []
        proxy._hand.sort(key=lambda x: x.sort_value(self._trump_suit))

        proxy._starting_player = idx_permutation.index(self._starting_player_pli)

        return proxy


"""
A simplified game context containing only what is necessary for the client side,
and not game logic
"""
class GameProxy:

    def __init__(self):
        self._state = None
        self._trump_suit = None
        self._starting_player = 0
        self._players = []
        self._cards = []
        self._hand = []


    @property
    def state(self):
        return self._state


    @property
    def trump_suit(self):
        return self._trump_suit


    @property
    def players(self):
        return self._players


    @property
    def hand(self):
        return self._hand


    @property
    def starting_player(self):
        return self._starting_player


    @property
    def cards(self):
        return self._cards


    def to_args(self):
        args = []

        args.append(self._state)
        args.append(self._trump_suit if self._trump_suit else "")
        args.append(str(self._starting_player))

        args += self._players
        args += [card.code for card in self._cards]

        args.append(str(len(self._hand)))
        args += [card.code for card in self._hand]

        return args


def from_args(args):

    proxy = GameProxy()

    idx = 0

    proxy._state = args[idx]
    idx += 1

    proxy._trump_suit = args[idx]
    idx += 1

    proxy._starting_player = int(args[idx])
    idx += 1

    proxy._players = args[idx: idx+4]
    idx += 4

    proxy._cards = [card.Card(code) for code in args[idx: idx+4]]
    idx += 4

    hand_count = int(args[idx])
    idx += 1
    proxy._hand = [card.Card(code) for code in args[idx: idx+hand_count]]
    idx += hand_count

    return proxy
