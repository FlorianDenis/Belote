#
# Copyright (C) Florian Denis - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited.
# Proprietary and confidential.
#

import logging
import pygame
import sys

from . import game


class GUI:

    def __init__(self):
        # Setup window
        self._w = 500
        self._h = 500
        self._win = pygame.display.set_mode((self._w, self._h))

        # GUI is not threaded, the runloop takes place in the main thread
        # This means run() won't return
        self._running = False

        pygame.display.set_caption("Belote")


    def run(self):
        self._running = True
        while self._running:

            # Redraw
            self._redraw()

            # Process input events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                    pygame.quit()

            # Process incoming actions events


    def _redraw(self):
        self._win.fill((255, 255, 255))
        pygame.display.update()
