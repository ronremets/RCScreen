"""
A user which is a collection of clients
"""

__author__ = "Ron Remets"

import threading


class User(object):
    """
    A user which is a collection of clients
    """
    def __init__(self, username, password, connector):
        self._unconnected_connections_lock = threading.Lock()
        self._connections_lock = threading.Lock()
        self._partner_lock = threading.Lock()
        self._tokens_lock = threading.Lock()
        # TODO: is this used?
        self._unconnected_connections = {}  # {name: connection}
        self._connections = {}  # {name: connection}
        self._tokens = {}
        self.connector = connector
        self.username = username
        self.password = password
        self.partner = None

    @property
    def tokens(self):
        """
        The tokens of connections
        NOTE: THIS RETURNS A REFERENCE AND NOT A COPY. ANY CHANGES TO
        THE RETURNED dict WILL CHANGE THE ACTUAL LIST
        :return: A reference to dict like {token: name}
        """
        with self._tokens_lock:
            return self._tokens

    @property
    def unconnected_connections(self):
        """
        The connections that were not completely connected
        NOTE: THIS RETURNS A REFERENCE AND NOT A COPY. ANY CHANGES TO
        THE RETURNED dict WILL CHANGE THE ACTUAL LIST
        :return: A reference to dict like {name: connection}
        """
        with self._unconnected_connections_lock:
            return self._unconnected_connections

    @property
    def connections(self):
        """
        The connections that were connected
        NOTE: THIS RETURNS A REFERENCE AND NOT A COPY. ANY CHANGES TO
        THE RETURNED dict WILL CHANGE THE ACTUAL LIST
        :return: A reference to the dict {name: connection}
        """
        with self._connections_lock:
            return self._connections

    @property
    def partner(self):
        with self._partner_lock:
            return self._partner

    @partner.setter
    def partner(self, value):
        with self._partner_lock:
            self._partner = value

    def add_token(self, token, name):
        """
        Remove a token from the tokens list.
        :param token: The token to remove
        :param name: The name of the connection the token belongs to
        """
        with self._tokens_lock:
            self._tokens[token] = self, name

    def remove_token(self, token):
        """
        Remove a token from the tokens list.
        :param token: The token to remove
        """
        with self._tokens_lock:
            self._tokens.pop(token)
