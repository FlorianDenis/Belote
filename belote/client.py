#
# Copyright (C) Florian Denis - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited.
# Proprietary and confidential.
#

import logging
import random
import socket
import sys

from . import constants
from . import packet
from . import player
from . import transport
from . import gui
from . import game

log = logging.getLogger(__name__)


class Client:

    def __init__(self, host, port, name):

        # Server info
        self._host = host
        self._port = port

        # Local player instance
        identifier = "{:x}".format(random.getrandbits(32))
        self._player = player.Player(identifier, name)


    def run(self):
        # Connect to server
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((self._host, self._port))
            log.info("Connection established with server {}:{}"
                .format(self._host, self._port))
        except:
            log.error("Unable to establish connection to server {}:{}"
                .format(self._host, self._port))
            sock.close()
            sys.exit(1)

        # Create transport
        self._transport = transport.Transport(sock)
        self._transport.on_recv = self.__recv
        self._transport.on_drop = self.__drop
        self._transport.run()

        # Register a new player
        self._register()

        # Create GUI
        self._gui = gui.GUI()
        self._gui.run()


    def _perform(self, opcode, *args):
        tx_packet = packet.Packet(constants.MessageType.COMMAND, opcode, *args)
        self._transport.send(tx_packet)


    def __drop(self, transport):
        log.error("Connection dropped with server")
        sys.exit(1)


    def _register(self):
        self._perform(
            constants.CommandOpcode.CREATE_PLAYER,
            self._player.identifier,
            self._player.name)


    def _handle_new_proxy(self, proxy):
        # Update UI!
        pass


    def __recv(self, transport, rx_packet):
        """
        Receive packet from server
        """
        if rx_packet.msg_type != constants.MessageType.NOTIF:
            log.warn("Cannot handle incoming message {}", rx_packet)
            return

        if rx_packet.opcode == constants.NotifOpcode.GAME_STATUS:
            proxy = game.from_args(rx_packet.args)
            self._handle_new_proxy(proxy)


    def stop(self):
        self._transport.stop()
