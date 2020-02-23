"""
Represents a session connected to a user
"""

__author__ = "Ron Remets"

import threading


class Connection(object):
    """
    Represents a session connected to a user
    """
    def __init__(self, connection_socket, connection_type, db_connection):
        self.db_connection = db_connection
        self.socket = connection_socket
        self.type = connection_type
        self._running_lock = threading.Lock()
        self._set_running(True)

    @property
    def running(self):
        """
        Check if the client is running.
        :return: True if it is, otherwise False
        """
        with self._running_lock:
            return self.__running

    def _set_running(self, value):
        with self._running_lock:
            self.__running = value

    def close(self, kill=False):
        """
        Close the client. After closing, the client object is useless
        and can not be used again.
        :param kill: kill the socket (see AdvanceSocket)
        """
        self._set_running(False)
        self._socket.close(kill=kill)
