"""
The connect screen.
"""

__author__ = "Ron Remets"

import logging
import threading
import time

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty
from kivy.clock import Clock

from communication.message import Message, MESSAGE_TYPES


class ConnectScreen(Screen):
    """
    The screen where the client connects to another client
    """
    partner_label = ObjectProperty()
    user_selector = ObjectProperty()
    controller_checkbox = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._app = App.get_running_app()

    def connect_to_partner(self):
        # TODO: run this on another thread and check progress in main
        #  thread
        # TODO: is main connected? check here or assume it is connected?
        logging.debug(f"MAIN:Sending set partner: {self._app.partner}")
        self._app.connection_manager.connections["main"].socket.send(Message(
            MESSAGE_TYPES["server interaction"],
            f"set partner\n{self._app.partner}"))
        response = self._app.connection_manager.connections["main"].socket.recv(block=True)
        response = response.get_content_as_text()
        logging.debug(f"MAIN:answer to partner: {response}")

    def _update_selection(self, instance, username):
        """
        Update partner's label to the new username.
        :param username: The partner's username.
        """
        logging.info(f"Selected partner: {username}")
        self.partner_label.text = username

    def start_user_selector(self):
        """
        Wait for the connection to start then start the user selector
        """
        while self._app.connection_manager.connections["get users"] is None:
            if not self._app.connection_manager.running:
                raise NotImplementedError()  # TODO: what happens when closed?
        connection = self._app.connection_manager.connections["get users"]
        while not connection.connected:
            if not self._app.connection_manager.running:
                raise NotImplementedError()  # TODO: what happens when closed?
        self.user_selector.start(connection)

    def on_enter(self):
        """
        Start all the components and connections
        """
        self._app.bind(partner=self._update_selection)
        self._app.connection_manager.add_connection(
            self._app.username,
            "get users",
            (True, True),
            "main",
            block=False)
        threading.Thread(target=self.start_user_selector).start()

    def on_pre_leave(self):
        """
        Close user selector and its connection.
        """
        logging.debug("starting to leave")
        self.user_selector.close()
        logging.warning("Trying to crash socket")
        try:
            self._app.connection_manager.close_connection("get users", True)
        except Exception as e:
            logging.error("socket error while closing: " + str(e))
        logging.debug("closed connection to get users")
