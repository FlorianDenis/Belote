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
from . import pli


log = logging.getLogger(__name__)


"""
Full game context holding the state of the current game for the server side
Contains all the logic to advance the game to next level
"""
class Game:

    State = Enum('State', [(a, a) for a in (
        'WAITING_FOR_PLAYERS',
        'ANNOUNCING',
        'ONGOING',
        'FINISHED',
    )], type=str)


    def __init__(self):
        # Array of joined-in players
        self._players = []

        # Map player -> array of card in hand
        self._hands = {}

        # Who started the current round (a "round" is 8 pli)
        self._starting_player = 0

        # The current pli being played
        self._current_pli = None

        # The previous pli played
        self._previous_pli = None

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
        if self._trump_suit is None:
            return Game.State.ANNOUNCING
        if self._round_ongoing:
            return Game.State.ONGOING
        return Game.State.FINISHED


    def _cut(self, deck):
        cut_idx = random.choice(range(len(deck)))
        return deck[cut_idx:] + deck[:cut_idx]


    def _deal(self, deck):

        ordered_players = [self._players[idx % 4] for idx in range(
            self._starting_player, self._starting_player + 4)]

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


    def _start_pli(self, starting_player):
        self._current_pli = pli.Pli(self._players, starting_player)

        self.on_status_changed()


    def _start_round(self):
        if self._round_ongoing:
            log.error("Invalid state to start new round")
            return

        self._round_ongoing = True

         # Reset values from previous round we want to keep while "Finished"
        self._trump_suit = None
        self._points = [0.0, 0.0]
        self._previous_pli = None
        self._deck = self._cut(self._deck)
        self._hands = self._deal(self._deck)

        self._start_pli(self._starting_player)


    def pick_trump(self, player, suit):
        if self.state != Game.State.ANNOUNCING:
            log.error("Can only pick the trump suit while announcing")
            return

        if not player is self._players[self._starting_player]:
            log.error("Only the starting player shall select the trump suit")
            return

        self._trump_suit = suit
        self.on_status_changed()


    def play_card(self, player, card):
        if self.state != Game.State.ONGOING:
            log.error("Invalid state to play card")
            return

        hand = self._hands[player]
        if not card in hand:
            log.error("Trying to play card not in player's hand")
            return

        if not self._current_pli.can_play_card(
            player, card, hand, self._trump_suit):
            log.error("Given player cannot play this card right now")
            return

        # Actually play the card
        self._current_pli.play_card(player, card)
        self._hands[player].remove(card)

        is_last_pli = len(self._hands[player]) == 0

        if self._current_pli.is_complete:
            if is_last_pli:
                # Round completed, will terminate the round in 2 seconds
                threading.Timer(2, self._finish_round).start()
                threading.Timer(10, self._start_round).start()
            else:
                # Hand completed, will reset the pli in 2 seconds
                threading.Timer(2, self._finish_pli).start()

        self.on_status_changed()


    def _finish_pli(self):

        # Find out who won it
        taking_player = self._current_pli.taking_player(self._trump_suit)
        taking_player_idx = self._players.index(taking_player)

        is_last_pli = len(self._hands[taking_player]) == 0

        points = (self._current_pli.total_points(self._trump_suit)
            + (10 if is_last_pli else 0))

        self._plis[taking_player_idx % 2].append(self._current_pli)
        self._points[taking_player_idx % 2] += points

        self._previous_pli = self._current_pli
=
        self._start_pli(taking_player_idx)


    def _reset_round(self):
        self._current_pli = None
        self._hands = {}
        self._plis = [[], []]
        self._starting_player = (self._starting_player + 1) % 4
        self._round_ongoing = False

        self.on_status_changed()


    def _finish_round(self):

        # Finish the last pli
        self._finish_pli()

        # Reasssemble the deck
        odd_cards = sum([pli.cards for pli in self._plis[0]], [])
        even_cards = sum([pli.cards for pli in self._plis[1]], [])
        self._deck = odd_cards + even_cards

        # Clean current round
        self._reset_round()


    def add_player(self, player):
        if self.state != Game.State.WAITING_FOR_PLAYERS:
            log.error("Attempting to add player to already full game")
            return

        self._players.append(player)

        if len(self._players) == 4:
            self._start_round()
        else:
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

        starting_player_idx = (self._players.index(
            self._current_pli.starting_player)
                if self._current_pli
            else self._starting_player)

        proxy._starting_player = idx_permutation.index(starting_player_idx)

        proxy._players = [
            self._players[idx].name if idx < len(self._players) else ""
                for idx in idx_permutation
        ]

        proxy._current_pli = [
            self._current_pli.card_played_by(self._players[idx])
                if self._current_pli and self._current_pli.card_played_by(
                    self._players[idx])
                else card.Card("")
            for idx in idx_permutation
        ]

        proxy._previous_pli = [
            self._previous_pli.card_played_by(self._players[idx])
                if self._previous_pli and self._previous_pli.card_played_by(self._players[idx])
                else card.Card("")
                for idx in idx_permutation
        ]

        proxy._hand = self._hands[player] if player in self._hands else []
        proxy._hand.sort(key=lambda x: x.sort_value(self._trump_suit))

        proxy._legal = [
            (1 if self._current_pli.is_card_legal(player ,card, proxy._hand,
                self._trump_suit) else 0)
                    if self._current_pli else 0
                for card in proxy._hand
            ]

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
        self._legal = []


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
    def legal(self):
        return self._legal


    @property
    def starting_player(self):
        return self._starting_player


    @property
    def current_pli(self):
        return self._current_pli

    @property
    def previous_pli(self):
        return self._previous_pli
    
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
        args += [card.code for card in self._previous_pli]

        args.append(str(len(self._hand)))
        args += [card.code for card in self._hand]
        args += [str(legal) for legal in self._legal]

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
    proxy._previous_pli = [card.Card(code) for code in args[idx: idx+4]]
    idx += 4

    hand_count = int(args[idx])
    idx += 1
    proxy._hand = [card.Card(code) for code in args[idx: idx+hand_count]]
    idx += hand_count
    proxy._legal = [int(legal) for legal in args[idx: idx+hand_count]]
    idx += hand_count

    return proxy
