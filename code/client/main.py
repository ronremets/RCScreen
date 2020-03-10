"""
This is the entry point of the client's application.
"""

__author__ = "Ron Remets"
import threading
import time
import logging

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty

from communication.advanced_socket import AdvancedSocket
from communication.message import Message, MESSAGE_TYPES
from communication import communication_protocol
# noinspection PyUnresolvedReferences
import ui

SERVER_ADDRESS = ("127.0.0.1", 2125)
logging.basicConfig(level=logging.DEBUG)


class RCScreenApp(App):
    """
    Responsible for the whole client's application.
    """
    username = StringProperty()
    password = StringProperty()
    is_controller = BooleanProperty()
    partner = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._connections_lock = threading.Lock()
        with self._connections_lock:
            self.__connections = dict()

    @property
    def connections(self):
        """
        :return: A dictionary with all the connections to the server
        """
        with self._connections_lock:
            return self.__connections

    def add_connection(self,
                       name,
                       buffer_state,
                       connection_type,
                       method="login",
                       address=SERVER_ADDRESS):
        """
        Add a connection to app. Only call this after sign in or log in.
        :param name: The name of the connection
        :param buffer_state: a tuple like
               (input is buffered, output is buffered)
        :param connection_type: The type of connection to report to
               the server
        :param method: Whether to sign up or log in
        :param address: The address to connect to
        """
        # TODO: maybe move the log in part to comm_protocol
        # TODO: add a way to add connections
        # TODO: connect with token you get in log in
        # TODO: ----------very important!!!!!!!----------------
        #          ADD A SOCKET TO MANAGE CONNECTIONS
        #         IT WILL CHECK WHETHER THEY NEED TO CONNECTED
        #         AND TELL THE SERVER THEY ARE TO SYNC IT
        #                    WITH THE SOCKET
        #       -----------------------------------------------
        if name in self.connections:
            raise ValueError("connection already exists")
        connection = AdvancedSocket(address)
        connection.start(True, True)
        logging.debug(f"Sending method: {method}")
        connection.send(Message(
            MESSAGE_TYPES["server interaction"],
            f"{method}".encode(communication_protocol.ENCODING)))
        logging.debug(f"Sent method")
        connection.send(Message(
            MESSAGE_TYPES["server interaction"],
            (f"{self.username}\n"
             f"{self.password}\n"
             f"{connection_type}\n"
             f"{name}").encode(
                communication_protocol.ENCODING)))
        logging.info("Receiving connection status")
        connection_status = connection.recv().get_content_as_text()
        logging.info(f"Connection status: {connection_status}")
        connection.send(Message(
            MESSAGE_TYPES["server interaction"],
            "Connected".encode(communication_protocol.ENCODING)))
        time.sleep(1)  # TODO: remove and replace with a main type socket syncing with the server
        connection.switch_state(*buffer_state)
        self.connections[name] = connection

    def close_connection(self, name, kill=False):  # TODO: kill or block?
        """
        Close a running connection
        :param name: The name of the connection
        :param kill: kill the threads?
        """
        logging.info(f"Closing connection {name}")
        self.connections[name].close(kill)  # TODO: parameters
        self.connections.pop(name)

    def build(self):
        """
        Builds the application.
        :return: The application object.
        """
        return Builder.load_file("RCScreen.kv")


if __name__ == '__main__':
    RCScreenApp().run()
