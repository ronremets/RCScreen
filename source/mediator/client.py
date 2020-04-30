"""
Has everything a client needs when connecting to the server.
"""
__author__ = "Ron Remets"

import threading


class Client(object):
    """
    Has everything a client needs when connecting to the server.
    """
    def __init__(self, user):
        self.user = user
        self._connections = {}
        self._connections_lock = threading.Lock()
        self._partner_lock = threading.Lock()
        self.partner = None

    @property
    def partner(self):
        """
        The client this client connects to
        :return: A client object
        """
        with self._partner_lock:
            return self._partner

    @partner.setter
    def partner(self, value):
        with self._partner_lock:
            self._partner = value

    def add_connection(self, connection):
        """
        Add a connection to the dict of connections.
        :param connection: The connection to add.
        :raise ValueError: If the connection already exists.
        """
        with self._connections_lock:
            if connection.name in self._connections.keys():
                raise ValueError("Connection already exists")
            self._connections[connection.name] = connection

    def remove_connection(self, connection):
        """
        Remove a connection from the client.
        :param connection: The connection to remove.
        """
        with self._connections_lock:
            self._connections.pop(connection.name)

    def get_connection(self, name):
        """
        Get a connection of the client.
        :param name: The cname of the connection to get.
        :return: The connection object.
        """
        with self._connections_lock:
            return self._connections[name]

    def has_connection(self, name):
        """
        Check if the client has a connection.
        :param name: The connection to check.
        :return: True if exists, False otherwise.
        """
        with self._connections_lock:
            return name in self._connections.keys()
