#
# Copyright (C) Florian Denis - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited.
# Proprietary and confidential.
#

from . import card
from . import player

"""
Pli abstraction
Contains the context and logic for:
 - Which card has been played in the current pli
 - Can a player play a certain card ?
 - Who is taking the pli so far ?
"""
class Pli:

    def __init__(self, players, starting_player_idx):

        # The array of all players around the table
        self._players = players

        # The index of the player that starts this pli
        self._starting_player_idx = starting_player_idx

        # A map of each card played
        self._cards = {}


    @property
    def _ordered_player_indices(self):
        return [
            (self._starting_player_idx + 0) % 4,
            (self._starting_player_idx + 1) % 4,
            (self._starting_player_idx + 2) % 4,
            (self._starting_player_idx + 3) % 4,
        ]


    @property
    def cards(self):
        # Return the array of cards played, in their played order
        return [self._cards[self._players[idx]]
            for idx in self._ordered_player_indices]


    @property
    def starting_player(self):
        return self._players[self._starting_player_idx]


    @property
    def is_complete(self):
        return len(self._cards) == 4


    def card_played_by(self, player):
        return self._cards[player] if player in self._cards  else None


    def can_play_card(self, player, card, current_hand):
        # Complete ?
        if self.is_complete:
            return False

        current_player_idx = self._ordered_player_indices[len(self._cards)]

        # This player's turn ?
        if player is not self._players[current_player_idx]:
            return False

        return True


    def play_card(self, player, card):
        self._cards[player] = card


    def taking_player(self, trump_suit):

        taking_card = None
        taking_player_idx = None
        for idx in self._ordered_player_indices:
            played_card = self._cards[self._players[idx]]
            if played_card.overtakes(taking_card, trump_suit):
                taking_card = played_card
                taking_player_idx = idx

        return self._players[taking_player_idx]


    def total_points(self, trump_suit):
        return sum([card.point_value(trump_suit) for card in self.cards])
