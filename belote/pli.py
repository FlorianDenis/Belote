#
# Copyright (C) Florian Denis - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited.
# Proprietary and confidential.
#

from . import card
from . import constants
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
        # Return the array of cards played so far, in their played order
        return [self._cards[self._players[idx]]
            for idx in self._ordered_player_indices
                if self._players[idx] in self._cards]


    @property
    def starting_player(self):
        return self._players[self._starting_player_idx]


    @property
    def is_empty(self):
        return len(self._cards) == 0


    @property
    def is_complete(self):
        return len(self._cards) == 4


    def card_played_by(self, player):
        return self._cards[player] if player in self._cards else None


    def is_card_legal(self, player, card, hand, trump_suit):

        # Empty, anything goes
        if self.is_empty:
            return True

        # Player has already played in this pli
        if player in self._cards:
            return False

        player_idx = self._players.index(player)

        # Otherwise, determine the required suit, and currently taking card
        required_suit = self.cards[0].suit
        taking_card = self.taking_card(trump_suit)
        taking_player_idx = self.taking_player_idx(trump_suit)

        hand_contains_required = any(card for card in hand
            if card.suit == required_suit)
        hand_contains_overtaking = any(card for card in hand
            if card.overtakes(taking_card, trump_suit))

        # If there are still cards of the required suit in the hand, only those
        # are legal
        if hand_contains_required:

            # If the card is not the required suit, it cannot be played
            if card.suit != required_suit:
                return False

            # If the required suit is trump, we need to figure out if we
            # have trumps of higher values available
            if (required_suit == trump_suit or
                trump_suit == constants.Trump.AT) and hand_contains_overtaking:
                return card.overtakes(taking_card, trump_suit)

            # The card is of the required suit and there is no requirements
            return True

        # At this point, the hand does not contain the required color.
        # If it still contains the trump suit, only those can be played
        # except: if the taking player is the player's partner!
        if hand_contains_overtaking and taking_player_idx % 2 != player_idx % 2:
            return card.overtakes(taking_card, trump_suit)

        # We contain neither the required color nor do we have to play
        # the trump suit: anything goes
        return True


    def can_play_card(self, player, card, hand, trump_suit):
        # Complete ?
        if self.is_complete:
            return False

        current_player_idx = self._ordered_player_indices[len(self._cards)]

        # This player's turn ?
        if player is not self._players[current_player_idx]:
            return False

        # This card legal ?
        return self.is_card_legal(player, card, hand, trump_suit)


    def play_card(self, player, card):
        self._cards[player] = card


    def taking_player_idx(self, trump_suit):
        taking_card = None
        taking_player_idx = None
        for idx in self._ordered_player_indices:

            if not self._players[idx] in self._cards:
                break

            played_card = self._cards[self._players[idx]]
            if played_card.overtakes(taking_card, trump_suit):
                taking_card = played_card
                taking_player_idx = idx

        return taking_player_idx


    def taking_player(self, trump_suit):
        return self._players[self.taking_player_idx(trump_suit)]


    def taking_card(self, trump_suit):
        return self._cards[self.taking_player(trump_suit)]


    def total_points(self, trump_suit):
        return sum([card.point_value(trump_suit) for card in self.cards])
