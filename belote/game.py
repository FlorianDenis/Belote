#
# Copyright (C) Florian Denis - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited.
# Proprietary and confidential.
#
"""
Main context holding the state of the current game
"""

class Game:

    def __init__(self):
        self.players = []
        self.on_status_changed = None
