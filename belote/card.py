#
# Copyright (C) Florian Denis - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited.
# Proprietary and confidential.
#

from . import constants

"""
Card arbstraction
Allows for easy sorting (by color and by value, depending on trump suit)
"""
class Card():

    regular_value_order = ['A', '10', 'K', 'Q', 'J','9', '8', '7']
    trump_value_order = ['J', '9', 'A', '10', 'K', 'Q', '8', '7']

    @property
    def code(self):
        return self._code


    def __init__(self, code):
        self._code = code
        self._suit = code[-1:]
        self._value = code[:-1]


    def __eq__(self, other):
        if not isinstance(other, Card):
            return NotImplemented
        return self.code == other.code


    def sort_value(self, trump_suit):
        is_trump = (trump_suit == self._suit)

        # Global order of each suit within one's game
        suit_order = ['H', 'C', 'D', 'S']

        # Order within the suit, depending if we are trump
        value_order = (Card.trump_value_order if is_trump
            else Card.regular_value_order)

        return suit_order.index(self._suit) * 10 + value_order.index(self._value)



all = [Card(code.value) for code in constants.CardCode]