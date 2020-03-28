#
# Copyright (C) Florian Denis - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited.
# Proprietary and confidential.
#

import random

"""
A remote Player context
"""
class Player:

    def __init__(self):
        self.identifier = "{:x}".format(random.getrandbits(32))
        self.name = None
