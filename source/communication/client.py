"""
Has everything a client needs when connecting to the server.
"""
__author__ = "Ron Remets"

import logging
import threading
import time

from communication.connection import ConnectionStatus
from communication.message import Message, MESSAGE_TYPES


class Client(object):
    """
    Has everything a client needs when connecting to the server.
    """
    def __init__(self, user):
        self.user = user
        self._connections = {}
        self._can_add_connections = True
        # self._connected = True
        self._connections_lock = threading.Lock()
        self._partner_lock = threading.Lock()
        # self._can_add_connections_lock = threading.Lock()
        # self._connected_lock = threading.Lock()
        self.partner = None

    # @property
    # def connected(self):
    #     """
    #     Whether the client is currently connected and can be a partner
    #     :return: A bool
    #     """
    #     with self._connected_lock:
    #         return self._connected

    @property
    def can_add_connections(self):
        """
        Whether the client is currently active and can receive new
        connections
        :return: A bool
        """
        with self._connections_lock:
            return self._can_add_connections

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

    # TODO: change name
    def stop_adding_connections(self):
        """
        Change the client status to stop adding connections
        """
        with self._connections_lock:
            self._can_add_connections = False

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

    def remove_connection(self, name):
        """
        Remove a connection from the client.
        :param name: The name of the connection to remove.
        """
        with self._connections_lock:
            self._connections.pop(name)

    def safe_remove_connection(self, name):
        """
        Remove a connection from the client if it exists. Other wise
        just return false
        :param name: The name of the connection to remove.
        :return: True if connection was removed, False if not
        """
        try:
            with self._connections_lock:
                self._connections.pop(name)
        except KeyError:
            return False
        else:
            return True

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

    def has_non_connector_connections(self):
        """
        Check whether the clients has any connections
        :return: True if is has connections, False otherwise
        """
        with self._connections_lock:
            connections = list(self._connections.keys())
            connections.remove("connector")
            return len(connections) > 0

    def get_all_connections(self):
        """
        Get a shallow copy of self._connections.keys() as a list
        :return: A list with all the connections.
        """
        with self._connections_lock:
            return list(self._connections.values())

    # def crash(self):
    #     """
    #     Close all the connections.
    #     """
    #     with self._connections_lock:
    #         for connection in self._connections:
    #             self.remove_connection(connection)
    #             connection.close()

    def close_connection(self, connection):
        """
        You need the connector to be connected on another thread for
        this to work! otherwise it will close the connection without
        telling the other side (like self.crash_connection).

        Close the connection normally by telling connector to tell the
        other side to close.
        :param connection: The connection to close
        """
        try:
            connector = self.get_connection("connector")
        except KeyError:
            self.crash_connection(connection)
            return

        logging.debug(
            f"CLIENT:shutting down connection: {connection.name}")
        connection.disconnect()
        logging.debug(
            f"CLIENT:connection {connection.name} disconnected")
        while (connector.status is ConnectionStatus.CONNECTED
               and connection.status is ConnectionStatus.DISCONNECTED):
            time.sleep(0)
        logging.debug(
            f"CLIENT:connection {connection.name} closing")
        self.remove_connection(connection.name)
        connection.close()
        logging.debug(
            f"CLIENT:connection {connection.name} closed")

    def crash_connection(self, connection):
        """
        Crash the connection by closing it without telling the connector
        :param connection: The connection to crash
        """
        # TODO: close/crash partner!!!

        # TODO: maybe check that connection is in client? Is it a
        #  reference to a connection not in the client?
        logging.debug(
            f"CLIENT:crashing connection: {connection.name}")
        connection.status = ConnectionStatus.DISCONNECTING
        logging.debug(
            f"CLIENT:connection {connection.name} disconnecting")
        connection.disconnect()
        connection.status = ConnectionStatus.CLOSING
        logging.debug(
            f"CLIENT:connection {connection.name} disconnected and closing")
        self.remove_connection(connection.name)
        connection.close()
        logging.debug(
            f"CLIENT:connection {connection.name} closed")

    def connector_close_connection(self,
                                   name,
                                   this_side):
        """
        The method the connector runs when closing a connection
        :param name: The name of the connection to run
        :param this_side: whether this side of the network started the
                          disconnect
        """

        # TODO: can crash if connection does not exists
        connection = self.get_connection(name)
        connector = self.get_connection("connector")
        if this_side:
            connector.socket.send(Message(
                MESSAGE_TYPES["server interaction"],
                f"close:{connection.name}"))
        # if connection.status is ConnectionStatus.NOT_STARTED:
        #     pass  # TODO: Can this even happen?
        # elif connection.status not in (ConnectionStatus.NOT_STARTED,
        #                                ConnectionStatus.CONNECTING,
        #                                ConnectionStatus.CONNECTED):
        #     pass  # TODO: crash since connection is dead or error or closing

        if connection.status == ConnectionStatus.CONNECTED:
            connection.status = ConnectionStatus.DISCONNECTING
        logging.debug(f"CONNECTIONS:Connector set {name} to disconnecting")
        # TODO: what if connector closes or server closes?
        #while self.running and connector.status is ConnectionStatus.CONNECTED:
        while True:
            time.sleep(0)
            # TODO: what if status is error?
            if connection.status is not ConnectionStatus.DISCONNECTING:
                break

        logging.debug(f"CONNECTIONS:{name} disconnected sending finished")

        connector.socket.send(Message(
            MESSAGE_TYPES["server interaction"],
            "finished"))

        # TODO: what if connector closes or server closes?
        #while self.running and connector.status is ConnectionStatus.CONNECTED:
        while True:
            time.sleep(0)
            response = connector.socket.recv(block=False)
            if response is not None:
                logging.debug(("CLIENT:Closing connector response: "
                              + response.get_content_as_text()))
                connection.status = ConnectionStatus.CLOSING
                logging.debug(
                    f"CONNECTIONS:Connector set {name} to closing")
                break

    def _connector_close_non_connector(self,
                                       this_side):
        """
        What the connector runs to close all connections that are not
         the connector
        :param this_side: whether this side of the network started the
                          disconnect
        """
        connector = self.get_connection("connector")
        try:
            for connection in self.get_all_connections():
                if connection.name != "connector":
                    self.connector_close_connection(connection.name, this_side)
        except Exception:
            logging.error("Error while disconnecting client", exc_info=True)
            logging.info(f"crashing client {self.user.username}")
            logging.info(f"client {self.user.username}'s connector is "
                         f"disconnecting")
            connector.status = ConnectionStatus.DISCONNECTING
            try:
                while self.has_non_connector_connections():
                    time.sleep(0)
            except Exception:
                logging.error("Error while crashing client",
                              exc_info=True)

    def connector_close_all_connections(self,
                                        this_side):
        """
        The method the connector runs when wanting to close all non
        connector connections and disconnect
        :param this_side: whether this side of the network started the
                          disconnect
        """
        # TODO: what about partner?
        # TODO: fix race condition here
        self.stop_adding_connections()
        connector = self.get_connection("connector")
        self._connector_close_non_connector(this_side)
        if this_side:
            connector.socket.send(Message(
                MESSAGE_TYPES["server interaction"],
                "disconnect:"),
                block_until_buffer_empty=True)
        # TODO: calling shutdown might prevent the socket from receiving
        #  the disconnect request
        connector.disconnect()
        logging.info(f"client {self.user.username}'s connector is "
                     f"disconnected")
        connector.status = ConnectionStatus.CLOSING
        logging.info(f"client {self.user.username}'s connector is "
                     f"closing")
        try:
            connector.close()
        except Exception:
            logging.info((f"error while closing connector of "
                          + str(self.user.username)),
                         exc_info=True)
        else:
            logging.info(
                f"client {self.user.username}'s connector is closed")
