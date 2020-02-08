"""
A user which is a collection of clients
"""

__author__ = "Ron Remets"

import threading


class User(object):
    """
    A user which is a collection of clients
    """
    def __init__(self, username, password):
        self.__connections = []
        self.username = username
        self.password = password
        self.partner = None
        self._connections_lock = threading.Lock()

    @property
    def connections(self):
        """
        A getter for the client list
        NOTE: THIS RETURNS A REFERENCE AND NOT A COPY. ANY CHANGES TO
        THE RETURNED LIST WILL CHANGE THE ACTUAL LIST
        :return: A reference to the clients list
        """
        with self._connections_lock:
            return self.__connections  # TODO: maybe make it private
