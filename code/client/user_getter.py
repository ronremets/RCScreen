"""
Gets the connected users from the server
"""
__author__ = "Ron Remets"

import threading
import time

from component import Component
from communication.message import Message, MESSAGE_TYPES
from communication.advanced_socket import ConnectionClosed


class UserGetter(Component):
    """
    Gets the connected users from the server
    """
    def __init__(self):
        super().__init__()
        self._name = "user getter"
        self._connection = None
        self._users_lock = threading.Lock()
        self._users = None

    @property
    def users(self):
        """
        The connected users
        :return: A list with all the users as strings
        """
        with self._users_lock:
            return self._users

    def _update(self):
        try:
            self._connection.socket.send(Message(
                MESSAGE_TYPES["server interaction"],
                "get all connected usernames"))
            users_packet = self._connection.socket.recv(block=True)
            time.sleep(3)
        except ConnectionClosed:
            return True  # Cancel the event TODO: implement this
        users = users_packet.get_content_as_text()
        with self._users_lock:
            self._users = users.split(", ")

    def start(self, connection):
        """
        Start getting the users from the server.
        :param connection: The connection to the server.
        """
        self._users = []
        self._connection = connection
        self._start()
