"""
A class to organize a connection
"""
__author__ = "Ron Remets"

import logging
import threading


class Connection(object):
    """
    A class to organize a connection
    """
    def __init__(self, name, socket, connection_type):
        self.name = name
        self.socket = socket
        self.type = connection_type
        self._running_lock = threading.Lock()
        self._connected_lock = threading.Lock()
        self.connected = False
        self._set_running(False)

    @property
    def running(self):
        """
        Check if the connection (socket) is running.
        :return: True if it is, otherwise False
        """
        with self._running_lock:
            return self._running

    def _set_running(self, value):
        with self._running_lock:
            self._running = value

    @property
    def connected(self):
        """
        Whether the socket is connected
        (Not if it is running, but if the buffers state were switched
        to the right state)
        :return: True if it is, otherwise False
        """
        with self._connected_lock:
            return self._connected

    @connected.setter
    def connected(self, value):
        with self._connected_lock:
            self._connected = value

    def start(self):
        """
        Start the connection by setting running to True
        """
        logging.info(f"CONNECTIONS:Starting connection {self.name}")
        self._set_running(True)

    def close(self, kill=False):
        """
        Close the connection by closing the socket
        :param kill: kill the socket (see AdvanceSocket)
        """
        logging.info(f"CONNECTION:Closing connection {self.name}")
        self.connected = False
        self._set_running(False)
        self.socket.shutdown(block=not kill)
        self.socket.close()
