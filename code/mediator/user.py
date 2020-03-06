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
        self._connections_lock = threading.Lock()
        self._partner_lock = threading.Lock()
        with self._connections_lock:  # TODO: is this necessary?
            self.__connections = {}
        self.username = username
        self.password = password
        self.partner = None

    @property
    def connections(self):
        """
        A getter for the client dict
        NOTE: THIS RETURNS A REFERENCE AND NOT A COPY. ANY CHANGES TO
        THE RETURNED dict WILL CHANGE THE ACTUAL LIST
        :return: A reference to the clients dict
        """
        with self._connections_lock:
            return self.__connections  # TODO: maybe make it private

    @property
    def partner(self):
        with self._partner_lock:
            return self.__partner

    @partner.setter
    def partner(self, value):
        with self._partner_lock:
            self.__partner = value
