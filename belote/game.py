#
# Copyright (C) Florian Denis - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited.
# Proprietary and confidential.
#

import logging


log = logging.getLogger(__name__)

"""
Full game context holding the state of the current game for the server side
Contains all the logic to advance the game to next level
"""
class Game:


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
    def is_full(self):
        return len(self._players) == 4


    @property
    def round_ongoing(self):
        return self._round_ongoing


    @property
    def is_ready_to_start_round(self):
        return self.is_full and not self.round_ongoing


    def _reset_round(self):
        self._cards = []
        self._hands = {}
        self._starting_player = (self._starting_player+ 1) % 4
        self._round_ongoing = False

        self.on_status_changed()


    def add_player(self, player):
        if self.is_full:
            log.error("Attempting to add player to already full game")
            return

        self._players.append(player)

        self.on_status_changed()


    def remove_player(self, player):
        if not player in self._players:
            log.error("Attempting to add player to already full game")
            return

        self._players.remove(player)

        if self.round_ongoing:
            log.info("Player left while in a round: resetting")
            _reset_round()

        self.on_status_changed()


    def proxy_for_player(self, player):
        if not player in self._players:
            log.error("Attempting to generate a proxy for a player not in game")
            return None

        proxy = GameProxy()

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
        self._players = []
        self._cards = []
        self._hand = []
        self._starting_player = 0
        self._round_ongoing = False


    def to_args(self):
        args = []

        args.append(str(len(self._players)))
        args += self._players

        args.append(str(len(self._cards)))
        args += self._cards

        args.append(str(len(self._hand)))
        args += self._hand

        args.append(str(self._starting_player))
        args.append(str(self._round_ongoing))

        return args


def from_args(args):

    proxy = GameProxy()

    idx = 0

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

    proxy._starting_player = int(args[idx])
    idx += 1

    proxy._round_ongoing = bool(args[idx])
    idx += 1

    return proxy
