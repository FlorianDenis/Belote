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

    def __init__(self, windowed):

        # Setup window
        if windowed:
            self._win = pygame.display.set_mode((840, 840))
        else:
            self._win = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

        # GUI is not threaded, the runloop takes place in the main thread
        # This means run() won't return
        self._running = False

        # Callbacks
        self.on_ready = None
        self.on_trump_picked = None
        self.on_card_picked = None

        # Position information for collision detection
        self._toolbar_rect = pygame.Rect(0, 0, 0, 0)
        self._card_rects = []
        self._trump_rects = []

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


    def _texture(self, name):
        path = os.path.dirname(__file__)
        texture_filename = '{}.png'.format(name)
        texture_path = os.path.join(path, 'resources', texture_filename)
        return pygame.image.load(texture_path)


    def _redraw(self, proxy):

        screen = Rect(
            origin = Point(0, 0),
            size = Size(self._win.get_width(), self._win.get_height()))

        game_area = Rect(center = screen.center, size = Size(800, 800))

        # Background: solid green color over the wholes screen
        background = pygame.Surface((screen.width, screen.height))
        background = background.convert()
        background.fill((80, 150, 15))

        self._win.blit(background, (screen.origin.x, screen.origin.y))

        # Toolbar: bottom of the screen
        toolbar_height = 40
        toolbar_rect = Rect(
            origin = Point(screen.min_x, screen.max_y - toolbar_height),
            size = Size(screen.width, toolbar_height))

        toolbar = pygame.Surface((toolbar_rect.width, toolbar_rect.height))
        toolbar = toolbar.convert()
        toolbar.fill((100, 100, 100))

        self._toolbar_rect = pygame.Rect(
            toolbar_rect.min_x, toolbar_rect.min_y,
            toolbar_rect.width, toolbar_rect.height)

        self._win.blit(toolbar, (toolbar_rect.origin.x, toolbar_rect.origin.y))

        if proxy is None:
            pygame.display.update()
            return

        font = pygame.font.SysFont('arial', 20)

        # Game status
        status = {
            game.Game.State.WAITING_FOR_PLAYERS: "Waiting...",
            game.Game.State.ANNOUNCING:          "Announcing...",
            game.Game.State.ONGOING:             "",
            game.Game.State.FINISHED:            "Finished",
        }

        status_text = font.render(status[proxy.state], 1, (255, 255, 255))
        status_origin = Point(
            toolbar_rect.min_x + 30,
            toolbar_rect.mid_y - status_text.get_height() / 2)

        self._win.blit(status_text, (status_origin.x, status_origin.y))


        # Points
        points = "us: {} - them: {}".format(
            proxy.player_points, proxy.enemy_points)
        points_text = font.render(points, 1, (255, 255, 255))
        points_origin = Point(
            toolbar_rect.max_x - 30 - points_text.get_width(),
            toolbar_rect.mid_y - points_text.get_height() / 2)

        self._win.blit(points_text, (points_origin.x, points_origin.y))


        # Hand
        card_spacing = 30
        card_size = Size(130, 200)
        small_card_size = Size(65, 100)

        num_cards_hand = len(proxy.hand)

        hand_zone_height = 200
        hand_zone_width = (num_cards_hand-1) * card_spacing + card_size.width

        hand_zone_center = Point(
            game_area.mid_x,
            game_area.max_y - (hand_zone_height / 2))

        hand_zone_rect = Rect(
            center = hand_zone_center,
            size = Size(hand_zone_width, hand_zone_height))

        self._card_rects = []

        for i in range(num_cards_hand):
            card_hilight = proxy.legal[i] and 1 - proxy.legal[i] in proxy.legal

            card_position = Rect(
                origin = Point(
                    hand_zone_rect.min_x + i * card_spacing,
                    hand_zone_rect.min_y - (30 if card_hilight else 0)),
                size = card_size)

            card_texture = self._texture(proxy.hand[i].code)
            card_texture = pygame.transform.scale(card_texture,
                (card_size.width, card_size.height))

            card_rect = pygame.Rect(
                card_position.origin.x, card_position.origin.y,
                card_size.width, card_size.height)

            self._card_rects.append(card_rect)

            self._win.blit(card_texture,
                (card_position.origin.x, card_position.origin.y))

        # Current pli
        main_play_area_size = Size(game_area.width, game_area.height - hand_zone_height)
        card_zone_rect = Rect(origin = game_area.origin, size = main_play_area_size)
        self.render_pli(proxy.current_pli, game_area.origin, main_play_area_size, card_size)

        # Previous pli
        # Displayed to the right of the player's hand
        previous_pli_size = Size(
            320,
            280
        )
        previous_pli_origin = Point(
            0,
            0
        )
        self.render_pli(
            proxy.previous_pli, 
            previous_pli_origin, 
            previous_pli_size, 
            small_card_size
        )




        # Player names
        player_names_contour = card_zone_rect.inset_by(50, 20)
        player_name_center = {
            0: player_names_contour.center_bottom,
            1: player_names_contour.center_right,
            2: player_names_contour.center_top,
            3: player_names_contour.center_left,
        }

        for idx in range(4):
            player_name = proxy.players[idx]

            # Add an indicator if this is the current "first" player
            if idx == self._game.starting_player:
                player_name = '• {} •'.format(player_name)

            player_text = font.render(player_name, 1, (255, 255, 255))
            player_text_rect = Rect(
                center = player_name_center[idx],
                size = Size(player_text.get_width(), player_text.get_height()))

            self._win.blit(player_text,
                (player_text_rect.origin.x, player_text_rect.origin.y))

        # Current Trump suit
        if proxy.trump_suit:
            trump_rect = Rect(origin = Point(10, 10), size = Size(50, 50))
            trump_texture = self._texture(proxy.trump_suit)
            trump_texture = pygame.transform.scale(trump_texture,
                (trump_rect.width, trump_rect.height))

            self._win.blit(trump_texture,
                (trump_rect.origin.x, trump_rect.origin.y))


        # Trump selection if necessary
        self._trump_rects = []
        if proxy.state == game.Game.State.ANNOUNCING \
            and proxy.starting_player == 0:

            trumps = [trump.value for trump in constants.Trump]

            trump_zone_contour = card_zone_rect.inset_by(200, 200)
            trump_center = {
                constants.Trump.H : trump_zone_contour.top_left,
                constants.Trump.S : trump_zone_contour.center_top,
                constants.Trump.C : trump_zone_contour.bottom_left,
                constants.Trump.D : trump_zone_contour.center_bottom,
                constants.Trump.AT: trump_zone_contour.top_right,
                constants.Trump.NT: trump_zone_contour.bottom_right,
            }

            for trump in trumps:
                trump_size = Size(150, 150)
                trump_texture = self._texture(trump)
                trump_texture = pygame.transform.scale(trump_texture,
                    (trump_size.width, trump_size.height))

                trump_rect = Rect(
                    center = trump_center[trump],
                    size = trump_size)

                self._trump_rects.append(pygame.Rect(
                    trump_rect.origin.x, trump_rect.origin.y,
                    trump_rect.width, trump_rect.height
                ))

                self._win.blit(trump_texture,
                    (trump_rect.origin.x, trump_rect.origin.y))

        pygame.display.update()

    # Create and appends the rect to self
    # Also apply the bit texture to the rects
    def render_pli(self, pli, origin, size, card_size):
        
        # if (size.width < card_size.width * 3) or (size.height < card_size.height * 3):
        #     print "render_pli: Sizes are incorrectly set - some cards may overlap :("
        
        card_zone_rect = Rect(origin = origin, size = size)
        card_zone_contour = card_zone_rect.inset_by(
            card_size.width + 25, 
            card_size.height - 25,
        )
        card_center = {
            0: card_zone_contour.center_bottom,
            1: card_zone_contour.center_right,
            2: card_zone_contour.center_top,
            3: card_zone_contour.center_left,
        }

        for idx in range(4):
            card = pli[idx]

            if not card.code:
                continue

            card_texture = self._texture(card.code)
            card_texture = pygame.transform.scale(card_texture,
                (card_size.width, card_size.height))

            card_rect = Rect(center = card_center[idx], size = card_size)

            self._win.blit(card_texture,
                (card_rect.origin.x, card_rect.origin.y))


    def _handle_click(self, event):

        # Picked a card ?
        for card in reversed(self._card_rects):
            if card.collidepoint(pygame.mouse.get_pos()):
                card_idx = self._card_rects.index(card)
                if card_idx < len(self._game.hand):
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
