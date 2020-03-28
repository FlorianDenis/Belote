#
# Copyright (C) Florian Denis - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited.
# Proprietary and confidential.
#

import logging

from enum import Enum


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


    def start_round(self):
        if self.state != Game.State.READY_TO_START:
            log.error("Invalid state to start new round")
            return

        self._round_ongoing = True
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

        proxy = GameProxy()

        proxy._state = self.state
        proxy._players = [player.name for player in self._players]
        proxy._cards = self._cards
        proxy._hand = self._hands[player] if player in self._hands else []
        proxy._starting_player = self._starting_player
        proxy._round_ongoing = self._round_ongoing

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


    def to_args(self):
        args = []

        args.append(self._state)
        args.append(str(self._starting_player))

        args.append(str(len(self._players)))
        args += self._players

        args.append(str(len(self._cards)))
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

    player_count = int(args[idx])
    idx += 1
    proxy._players = args[idx: idx+player_count]
    idx += player_count

    cards_count = int(args[idx])
    idx += 1
    proxy._cards = args[idx: idx+cards_count]
    idx += cards_count

    hand_count = int(args[idx])
    idx += 1
    proxy._hand = args[idx: idx+hand_count]
    idx += hand_count

    return proxy
