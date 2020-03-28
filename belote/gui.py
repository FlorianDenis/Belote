#
# Copyright (C) Florian Denis - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited.
# Proprietary and confidential.
#

import logging
import pygame
import os

from . import constants
from . import game

from . geometry import *


class GUI:

    def __init__(self):
        # Setup window
        self._w = 800
        self._h = 800
        self._win = pygame.display.set_mode((self._w, self._h))

        # GUI is not threaded, the runloop takes place in the main thread
        # This means run() won't return
        self._running = False

        # Callbacks
        self.on_ready = None
        self.on_trump_picked = None
        self.on_card_picked = None

        self._game = None

        pygame.display.set_caption("Belote")
        pygame.init()


    def set_game(self, game):
        self._game = game


    def run(self):
        self._running = True
        while self._running:

            # Redraw
            self._redraw(self._game)

            # Process input events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                    pygame.quit()
                    os._exit(1)
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self._handle_click(event)


    def _card_texture(self, card):
        path = os.path.dirname(__file__)
        texture_name = 'resources/{}.png'.format(card)
        texture_path = os.path.join(path, texture_name)
        return pygame.image.load(texture_path)


    def _redraw(self, proxy):

        screen = Rect(Point(0, 0), Size(self._w, self._h))

        # Background: solid green color
        background_rect = screen

        background = pygame.Surface(
            (background_rect.size.w, background_rect.size.h))
        background = background.convert()
        background.fill((80, 150, 15))

        self._win.blit(background,
            (background_rect.origin.x, background_rect.origin.y))

        # Toolbar: bottom of the screen
        toolbar_height = 40
        toolbar_rect = Rect(
            Point(screen.minX, screen.maxY - toolbar_height),
            Size(screen.size.w, toolbar_height))

        toolbar = pygame.Surface((toolbar_rect.size.w, toolbar_rect.size.h))
        toolbar = toolbar.convert()
        toolbar.fill((100, 100, 100))

        self._toolbar_rect = pygame.Rect(
            toolbar_rect.minX, toolbar_rect.minY,
            toolbar_rect.size.w, toolbar_rect.size.h)

        self._win.blit(toolbar, (toolbar_rect.origin.x, toolbar_rect.origin.y))

        if proxy is None:
            pygame.display.update()
            return

        font = pygame.font.SysFont('arial', 20)

        # Game status
        status = {
            game.Game.State.WAITING_FOR_PLAYERS: "Waiting...",
            game.Game.State.READY_TO_START:      "Ready",
            game.Game.State.ANNOUNCING:          "Announcing...",
            game.Game.State.ONGOING:              "",
        }

        status_text = font.render(status[proxy.state], 1, (255, 255, 255))
        status_origin = Point(
            toolbar_rect.minX + 30,
            toolbar_rect.midY - status_text.get_height()/2)

        self._win.blit(status_text, (status_origin.x, status_origin.y))


        # Hand
        card_spacing = 30
        card_size = Size(130, 200)

        num_cards_hand = len(proxy.hand)

        hand_zone_height = 200
        hand_zone_width = (num_cards_hand-1) * card_spacing + card_size.w

        hand_zone_center = Point(
            screen.midX,
            screen.maxY - toolbar_height - (hand_zone_height / 2))

        hand_zone_rect = Rect(
            Point(
                hand_zone_center.x - hand_zone_width / 2,
                hand_zone_center.y - hand_zone_height / 2),
            Size(hand_zone_width, hand_zone_height))


        self._card_rects = []

        for i in range(num_cards_hand):
            card_position = Rect(
                Point(
                    hand_zone_rect.minX + i * card_spacing,
                    hand_zone_rect.minY),
                card_size)

            card_texture = self._card_texture(proxy.hand[i])
            card_texture = pygame.transform.scale(card_texture,
                (card_size.w, card_size.h))

            card_rect = pygame.Rect(
                card_position.origin.x, card_position.origin.y,
                card_size.w, card_size.h)

            self._card_rects.append(card_rect)

            self._win.blit(card_texture,
                (card_position.origin.x, card_position.origin.y))

        # Cards
        card_zone_rect = Rect(
            Point(screen.minX, screen.minY),
            Size(screen.size.w, hand_zone_rect.minY - screen.minY))

        card_zone_inset = Size(250, 150)
        card_zone_contour = Rect(
            Point(
                card_zone_rect.minX + card_zone_inset.w,
                card_zone_rect.minY + card_zone_inset.h),
            Size(
                card_zone_rect.size.w - 2 * card_zone_inset.w,
                card_zone_rect.size.h - 2 * card_zone_inset.h)
        )
        card_center = {
            0: Point(card_zone_contour.midX, card_zone_contour.maxY),
            1: Point(card_zone_contour.maxX, card_zone_contour.midY),
            2: Point(card_zone_contour.midX, card_zone_contour.minY),
            3: Point(card_zone_contour.minX, card_zone_contour.midY),
        }

        for idx in range(4):
            card = proxy.cards[idx]

            if card is "":
                continue

            card_texture = self._card_texture(card)
            card_texture = pygame.transform.scale(card_texture,
                (card_size.w, card_size.h))

            card_origin = Point(
                card_center[idx].x - card_size.w / 2,
                card_center[idx].y - card_size.h / 2)

            self._win.blit(card_texture,
                (card_origin.x, card_origin.y))


        # Player names
        player_names_inset = Size(50, 20)
        player_names_contour = Rect(
            Point(
                card_zone_rect.minX + player_names_inset.w,
                card_zone_rect.minY + player_names_inset.h),
            Size(
                card_zone_rect.size.w - 2 * player_names_inset.w,
                card_zone_rect.size.h - 2 * player_names_inset.h)
        )
        player_name_center = {
            0: Point(player_names_contour.midX, player_names_contour.maxY),
            1: Point(player_names_contour.maxX, player_names_contour.midY),
            2: Point(player_names_contour.midX, player_names_contour.minY),
            3: Point(player_names_contour.minX, player_names_contour.midY),
        }

        for idx in range(4):
            player_name = proxy.players[idx]

            # Add an indicator if this is the current "first" player
            if idx == self._game.starting_player:
                player_name = '• {} •'.format(player_name)

            player_text = font.render(player_name, 1, (255, 255, 255))
            player_text_origin = Point(
                player_name_center[idx].x - player_text.get_width() / 2,
                player_name_center[idx].y - player_text.get_height() / 2)

            self._win.blit(player_text,
                (player_text_origin.x, player_text_origin.y))

        # Trump selection if necessary
        self._trump_rects = []
        if (proxy.state == game.Game.State.ANNOUNCING
            and proxy.starting_player == 0):

            trumps = [trump.value for trump in constants.Trump]

            for idx in range(len(trumps)):
                suit_size = Size(150, 150)
                suit_texture = self._card_texture(trumps[idx])
                suit_texture = pygame.transform.scale(suit_texture,
                    (suit_size.w, suit_size.h))

                suit_origin = Point(
                    card_center[idx].x - suit_size.w / 2,
                    card_center[idx].y - suit_size.h / 2)

                self._trump_rects.append(pygame.Rect(
                    suit_origin.x, suit_origin.y,
                    suit_size.w, suit_size.w
                ))

                self._win.blit(suit_texture,
                    (suit_origin.x, suit_origin.y))

        pygame.display.update()


    def _handle_click(self, event):

        # Picked a card ?
        for card in reversed(self._card_rects):
            if card.collidepoint(pygame.mouse.get_pos()):
                card_idx = self._card_rects.index(card)
                self.on_card_picked(self._game.hand[card_idx])
                return

        # Picked a trump
        trumps = [trump.value for trump in constants.Trump]
        for trump in self._trump_rects:
            if trump.collidepoint(pygame.mouse.get_pos()):
                trump_idx = self._trump_rects.index(trump)
                self.on_trump_picked(trumps[trump_idx])
                return

        # Clicked ready ? (or the whole toolbar for that matter...)
        if self._toolbar_rect.collidepoint(pygame.mouse.get_pos()):
            self.on_ready()
            return
