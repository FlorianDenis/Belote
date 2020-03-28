#
# Copyright (C) Florian Denis - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited.
# Proprietary and confidential.
#

import random

"""
A single Player context
"""
class Player:

    @property
    def name(self):
        return self._name


    @property
    def identifier(self):
        return self._identifier


    def __init__(self, identifier, name):
        self._identifier = identifier
        self._name = name
