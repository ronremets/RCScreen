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
        self._connections_lock = threading.Lock()
        self._partner_lock = threading.Lock()
        self._tokens_lock = threading.Lock()
        self._connections = {}  # {name: connection}
        self._tokens = {}
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

    def add_connection(self, connection):
        """
        Add a connection to the dict of connections
        :param connection: The connection to add
        """
        with self._connections_lock:
            self._connections[connection.name] = connection

    def add_token(self, token, name):
        """
        Add a new token.
        :param token: The token to remove
        :param name: The name of the connection the token belongs to
        """
        with self._tokens_lock:
            self._tokens[token] = name

    def validate_token(self, token, name):
        """
        Make sure a token is correct and disable it
        :param token: The token in bytes
        :param name: The name of the connection of the token
        :raise ValueError: If token does not exists or does not belong
                           to the connection
        """
        with self._tokens_lock:
            print(repr(self._tokens), repr(token))
            if token not in self._tokens:
                raise ValueError("Token does not exists")
            elif self._tokens[token] != name:
                raise ValueError("Token does not belong to connection")
            self._tokens.pop(token)
