#
# Copyright (C) Florian Denis - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited.
# Proprietary and confidential.
#

import logging
import socket
import sys

from . import constants
from . import packet
from . import transport
from . import gui

log = logging.getLogger(__name__)


class Client:

    def __init__(self, host, port):

        # Callbacks
        self._host = host
        self._port = port


    def run(self):

        # Connect to server
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((self._host, self._port))
            log.debug("Connection established with server {}:{}"
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

        # Create GUI
        self._gui = gui.GUI()
        self._gui.run()


    def perform(self, action, *args):
        tx_packet = packet.Packet(action, *args)
        self._transport.send(tx_packet)


    def __drop(self, transport):
        log.error("Connection dropped with server")
        sys.exit(1)


    def __recv(self, transport, rx_packet):
        """
        Receive packet from server
        """

        # TODO: stuff


    def disconnect(self):
        self._transport.stop()
