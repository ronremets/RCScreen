"""
A class to organize a connection
"""
__author__ = "Ron Remets"

import enum
import logging
import threading


class ConnectionStatus(enum.Enum):
    """
    The possible statuses of a connection
    """
    NOT_STARTED = enum.auto()
    CONNECTING = enum.auto()
    CONNECTED = enum.auto()
    DISCONNECTING = enum.auto()
    DISCONNECTED = enum.auto()
    CLOSING = enum.auto()
    CLOSED = enum.auto()
    ERROR = enum.auto()


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
        self._status_lock = threading.Lock()
        self.status = ConnectionStatus.NOT_STARTED
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

    @property
    def status(self):
        """
        What the connection is currently doing
        :return: A ConnectionStatus enum value
        """
        with self._status_lock:
            return self._status

    @status.setter
    def status(self, value):
        with self._status_lock:
            self._status = value

    def start(self):
        """
        Start the connection by setting running to True
        """
        logging.info(f"CONNECTIONS:Starting connection {self.name}")
        self._set_running(True)
        #self.status = ConnectionStatus.CONNECTING

    def disconnect(self):
        """
        close the threads that might crash if the other side closes.
        """
        self.socket.shutdown()
        self.status = ConnectionStatus.DISCONNECTED

    def close(self):
        """
        Close the connection.
        """
        self.socket.close()
        self.status = ConnectionStatus.CLOSED
