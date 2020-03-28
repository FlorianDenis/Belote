#
# Copyright (C) Florian Denis - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited.
# Proprietary and confidential.
#

"""
Provides a way to send / receive packets through a socket
"""


import logging
import queue
import socket
import threading

from . import packet

log = logging.getLogger(__name__)


class Transport:

    def __init__(self, socket):
        # Callbacks
        self.on_recv = None
        self.on_drop = None

        # Socket
        self._sock = socket
        self._sock_alive = True

        # TX queue
        self._tx_queue = queue.Queue()
        self._tx_queue_not_empty = threading.Event()

        # TX and RX threads
        self._running = False
        self._tx_thread = threading.Thread(target=self.__tx)
        self._rx_thread = threading.Thread(target=self.__rx)
        self._tx_thread.deamon = True
        self._rx_thread.deamon = True


    def run(self):
        # start TX and RX threads
        self._running = True
        self._tx_thread.start()
        self._rx_thread.start()


    def stop(self):
        self._running = False

        if self._sock_alive:
            self._sock.shutdown(socket.SHUT_RDWR)
            self._sock.close()

        current_thread = threading.current_thread()
        if self._tx_thread.is_alive() and current_thread is not self._tx_thread:
            self._tx_thread.join()

        if self._rx_thread.is_alive() and current_thread is not self._rx_thread:
            self._rx_thread.join()


    def __tx(self):
        """
        send pending packets from queue
        """

        while self._running:

            # Wait for pending events
            tx = self._tx_queue_not_empty.wait(timeout=1)

            if not tx: continue

            tx_packet = self._tx_queue.get()
            if self._tx_queue.empty():
                self._tx_queue_not_empty.clear()

            tx_bytes = tx_packet.to_bytes()
            self._sock.sendall(tx_bytes)

            log.debug("-->  {}".format(str(tx_packet)))


    def __rx_error(self):
        self._sock_alive = False
        if not self._running:
            return
        log.error("Connection dropped")
        if self.on_drop:
            self.on_drop(self)


    def __rx(self):
        """
        receive packets from socket
        """

        while self._running:
            try:
                rx_bytes = self._sock.recv(16384)
            except:
                rx_bytes = None

            if not rx_bytes:
                return self.__rx_error()

            # We might read several packets at once, let's separate
            while len(rx_bytes):

                idx = rx_bytes.find(packet.MESSAGE_SEP)

                rx_packet = packet.from_bytes(rx_bytes[:idx+1])
                log.debug("<--  {}".format(str(rx_packet)))

                self.on_recv(self, rx_packet)
                rx_bytes = rx_bytes[idx+1:]


    def send(self, tx_packet):
        self._tx_queue.put(tx_packet)
        self._tx_queue_not_empty.set()
