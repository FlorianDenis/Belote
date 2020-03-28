#
# Copyright (C) Florian Denis - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited.
# Proprietary and confidential.
#

import logging
import socket
import threading

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
            self.player     = player.Player()


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

        # Client accepting thread
        self._running = False
        self._thread = threading.Thread(
            target=self.__accept_incoming)
        self._thread.deamon = True


    def __lookup_link(self, transport=None):
        for link in self._links:
            if transport and link.transport is transport:
                return link
        return None


    def run(self):
        self._running = True
        self._thread.start()


    def stop(self):
        self._running = False

        current_thread = threading.current_thread()
        if self._thread.is_alive() and current_thread is not self._thread:
            self._thread.join()

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


    def __recv(self, transport, rx_packet):
        # TODO: Handle incoming packet
        pass


    def __drop(self, transport):
        link = self.__lookup_link(transport=transport)
        if not link:
            log.error('Lost connection on unknown link')
            return
        log.warning("Lost connection to {}".format(link.addr))

        # Remove the link from the array
        self._links.remove(link)

        link.transport.stop()


    def __broadcast_game_status(self):
        # TODO
        pass
