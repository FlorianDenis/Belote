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
        # Array of joined-in players
        self._players = []

        # Map player -> array of card in hand
        self._hands = {}

        # Map player -> card played (currently on the table)
        self._current_pli = {}

        # Who started the current round, and the current pli
        self._starting_player_round = 0
        self._starting_player_pli = 0

        # By team (even/odd), won pli so far and point total
        self._plis = [[], []]
        self._points = [0.0, 0.0]

        # Misc
        self._trump_suit = None

        self._deck = card.all
        random.shuffle(self._deck)

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


    def _cut(self, deck):
        cut_idx = random.choice(range(len(deck)))
        return deck[cut_idx:] + deck[:cut_idx]


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

        self._deck = self._cut(self._deck)
        self._hands = self._deal(self._deck)

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

        # Reset the score from the previous match
        self._points = [0.0, 0.0]

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

        current_player_idx = (
            self._starting_player_pli + len(self._current_pli)) % 4
        if player is not self._players[current_player_idx]:
            log.error("Not player's turn")
            return

        hand = self._hands[player]
        if not card in hand:
            log.error("Trying to play card not in player's hand")
            return

        if player in self._current_pli:
            log.error("Player already played")
            return

        self._hands[player].remove(card)
        self._current_pli[player] = card

        if len(self._current_pli) == 4 and len(self._hands[player]) == 0:
            # Round completed, will terminate the round in 2 seconds
            threading.Timer(2, self._finish_round).start()

        elif len(self._current_pli) == 4:
            # Hand completed, will reset the pli in 2 seconds
            threading.Timer(2, self._finish_pli).start()

        self.on_status_changed()


    def _finish_pli(self):

        # Find out who won it
        ordered_players_idx = [
            (self._starting_player_pli + 0) % 4,
            (self._starting_player_pli + 1) % 4,
            (self._starting_player_pli + 2) % 4,
            (self._starting_player_pli + 3) % 4,
        ]

        overtaking_card = None
        overtaking_player_idx = None
        for idx in ordered_players_idx:
            played_card = self._current_pli[self._players[idx]]
            if played_card.overtakes(overtaking_card, self._trump_suit):
                overtaking_card = played_card
                overtaking_player_idx = idx

        overtaking_player = self._players[overtaking_player_idx]
        is_last_pli = len(self._hands[overtaking_player]) == 0

        pli = self._current_pli.values()
        points = sum([card.point_value(self._trump_suit) for card in pli]) + (
            10 if is_last_pli else 0)

        self._plis[overtaking_player_idx % 2] += pli
        self._points[overtaking_player_idx % 2] += points
        self._current_pli = {}
        self._starting_player_pli = overtaking_player_idx

        self.on_status_changed()


    def _reset_round(self):
        self._current_pli = {}
        self._hands = {}
        self._plis = [[], []]
        self._starting_player_round = (self._starting_player_round + 1) % 4
        self._starting_player_pli = self._starting_player_round
        self._round_ongoing = False
        self._trump_suit = None

        for player in self._players:
            player.set_ready(False)

        self.on_status_changed()


    def _finish_round(self):

        # Finish the last pli
        self._finish_pli()

        # Reasssemble the deck
        self._deck = self._plis[0] + self._plis[1]

        # Clean current round
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
        proxy._player_points = round(self._points[(player_index % 2)])
        proxy._enemy_points  = round(self._points[(player_index + 1) % 2])

        proxy._starting_player = idx_permutation.index(self._starting_player_pli)

        proxy._players = [
            self._players[idx].name if idx < len(self._players) else ""
                for idx in idx_permutation
        ]

        proxy._current_pli = [
            self._current_pli[self._players[idx]]
                if idx < len(self._players) and self._players[idx] in self._current_pli
                    else card.Card("")
                for idx in idx_permutation
        ]

        proxy._hand = self._hands[player] if player in self._hands else []
        proxy._hand.sort(key=lambda x: x.sort_value(self._trump_suit))

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
        self._player_points = 0
        self._enemy_points = 0
        self._players = []
        self._current_pli = []
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
    def current_pli(self):
        return self._current_pli


    @property
    def player_points(self):
        return self._player_points


    @property
    def enemy_points(self):
        return self._enemy_points


    def to_args(self):
        args = []

        args.append(self._state)
        args.append(self._trump_suit if self._trump_suit else "")
        args.append(str(self._player_points))
        args.append(str(self._enemy_points))
        args.append(str(self._starting_player))

        args += self._players
        args += [card.code for card in self._current_pli]

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

    proxy._player_points = int(args[idx])
    idx += 1

    proxy._enemy_points = int(args[idx])
    idx += 1

    proxy._starting_player = int(args[idx])
    idx += 1

    proxy._players = args[idx: idx+4]
    idx += 4

    proxy._current_pli = [card.Card(code) for code in args[idx: idx+4]]
    idx += 4

    hand_count = int(args[idx])
    idx += 1
    proxy._hand = [card.Card(code) for code in args[idx: idx+hand_count]]
    idx += hand_count

    return proxy
