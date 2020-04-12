#
# Copyright (C) Florian Denis - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited.
# Proprietary and confidential.
#

import logging
import queue
import socket
import threading

from . import card
from . import constants
from . import packet
from . import player
from . import game
from . import transport


log = logging.getLogger(__name__)


class Server:

    class Link:

        def __init__ (self, addr, transport):
            self.addr       = addr
            self.transport  = transport
            self.player     = None


    def __init__(self, port):

        # Current game context
        self._game = game.Game()
        self._game.on_status_changed = self.__broadcast_game_status

        # Init accept socket
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(('', port))

        # Array of Server.Link instances
        self._links = []

        self._running = False

        # RX queue
        self._rx_queue = queue.Queue()
        self._rx_queue_not_empty = threading.Event()

        # Client accepting thread
        self._accepting_thread = threading.Thread(
            target=self.__accept_incoming)
        self._accepting_thread.deamon = True

        # Incoming packet handling thread
        self._handling_thread = threading.Thread(
            target=self.__handle_packet)
        self._handling_thread.deamon = True


    def __lookup_link(self, transport=None):
        for link in self._links:
            if transport and link.transport is transport:
                return link
        return None


    def run(self):
        self._running = True
        self._handling_thread.start()
        self._accepting_thread.start()


    def stop(self):
        self._running = False

        current_thread = threading.current_thread()

        if self._accepting_thread.is_alive() and \
            current_thread is not self._accepting_thread:
            self._accepting_thread.join()

        if self._handling_thread.is_alive() and \
            current_thread is not self._handling_thread:
            self._handling_thread.join()

        for link in self._links:
            link.transport.stop()
        self._links = []

        self._sock.shutdown(socket.SHUT_RDWR)
        self._sock.close()


    def __accept_incoming(self):
        while self._running:
            self._sock.listen(5)
            try:
                sock, addr = self._sock.accept()
            except:
                log.error("Could not establish connection to client: {}"
                    .format(sys.exc_info()[0]))
                continue

            log.info("Accepted incoming client connection on {}".format(addr))

            trans = transport.Transport(sock)
            trans.on_recv = self.__recv
            trans.on_drop = self.__drop

            self._links.append(Server.Link(addr, trans))
            trans.run()


    def _handle_command(self, link, rx_cmd):
        # Create a new player for current game
        if rx_cmd.opcode == constants.CommandOpcode.CREATE_PLAYER:
            # Add a new player to current game
            if link.player is None:
                link.player = player.Player(rx_cmd.args[0], rx_cmd.args[1])
                self._game.add_player(link.player)

        # Pick the trump color
        if rx_cmd.opcode == constants.CommandOpcode.PICK_TRUMP:
            if link.player is None:
                return
            self._game.pick_trump(link.player, rx_cmd.args[0])

        # Player plays a given card
        if rx_cmd.opcode == constants.CommandOpcode.PLAY_CARD:
            if link.player is None:
                return
            self._game.play_card(link.player, card.Card(rx_cmd.args[0]))


    def __handle_packet(self):
        while self._running:
            # Wait for incoming commands
            rx = self._rx_queue_not_empty.wait(timeout=1)

            if not rx: continue

            (rx_packet, link) = self._rx_queue.get()
            if self._rx_queue.empty():
                self._rx_queue_not_empty.clear()

            # Server only needs to handle commands for now
            if rx_packet.msg_type != constants.MessageType.COMMAND:
                log.warn("Unhandled packet: {}", str(rx_packet))
                return

            self._handle_command(link, rx_packet)


    def __recv(self, transport, rx_packet):
        # Do not process right here; set on the queue so that all packets can
        # be processed by the same thread
        link = self.__lookup_link(transport=transport)
        self._rx_queue.put((rx_packet, link))
        self._rx_queue_not_empty.set()


    def __drop(self, transport):
        link = self.__lookup_link(transport=transport)
        if not link:
            log.error('Lost connection on unknown link')
            return
        log.warning("Lost connection to {}".format(link.addr))

        # Remove the link from the array
        self._links.remove(link)
        if link.player:
            self._game.remove_player(link.player)

        link.transport.stop()


    def __broadcast_game_status(self):
        # Generate a proxy tailored to each client and send
        for link in self._links:
            proxy = self._game.proxy_for_player(link.player)
            if not proxy:
                continue
            tx_packet = packet.Packet(
                constants.MessageType.NOTIF,
                constants.NotifOpcode.GAME_STATUS,
                *proxy.to_args())
            link.transport.send(tx_packet)
