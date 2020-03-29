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

    regular_order = ['A', '10', 'K', 'Q', 'J', '9', '8', '7']
    trump_order = ['J', '9', 'A', '10', 'K', 'Q', '8', '7']

    regular_points = {
         'A': 11,
        '10': 10,
         'K': 4,
         'Q': 3,
         'J': 2,
         '9': 0,
         '8': 0,
         '7': 0,
    }

    trump_points = {
         'J' : 20,
         '9' : 14,
         'A' : 11,
        '10' : 10,
         'K' : 4,
         'Q' : 3,
         '8' : 0,
         '7' : 0,
    }

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
        value_order = (Card.trump_order if is_trump else Card.regular_order)

        return suit_order.index(self._suit) * 10 + value_order.index(self._value)


    def point_value(self, trump_suit):

        is_trump = (trump_suit == self._suit)

        points =  (Card.trump_points if is_trump else Card.regular_points)

        return float(points[self._value])


    def overtakes(self, other, trump_suit):
        if other is None:
            return True

        is_trump = (trump_suit == self._suit)
        other_trump = (trump_suit == other._suit)

        # The trump always wins against anything else
        if is_trump != other_trump:
            return is_trump

        # Are we the right suit ?
        if self._suit != other._suit:
            return False

        value_order = (Card.trump_order if is_trump else Card.regular_order)

        return value_order.index(self._value) < value_order.index(other._value)



all = [Card(code.value) for code in constants.CardCode]
