"""
A class to store the clients data.
"""

__author__ = "Ron Remets"

import threading


class Client(object):
    """
    Stores clients data.
    """
    def __init__(self, user):
        self.user = user
        self._sockets = []  # list of tuples (socket, socket_type)
        self._sockets_lock = threading.Lock()
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

    def __str__(self):
        output = (f"running: {self.running}\n"
                  f"user: {self.user}\n")
        for socket in self._sockets:
            output += str(socket) + "\n"
        return output

    def _set_running(self, value):
        with self._running_lock:
            self.__running = value

    def add_socket(self, socket, socket_type):
        """
        Add a socket to the client.
        :param socket: the AdvanceSocket to add
        :param socket_type: The type of socket to add
        """
        with self._sockets_lock:
            self._sockets.append((socket, socket_type))

    def close(self, kill=False):
        """
        Close the client. After closing, the client object is useless
        and can not be used again.
        :param kill: kill all the sockets (see AdvanceSocket)
        """
        self._set_running(False)
        for socket, _ in self._sockets:
            socket.close(kill=kill)
