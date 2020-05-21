"""
The connect screen.
"""

__author__ = "Ron Remets"

import logging

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty


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

    def connect(self):
        """
        Start to connect to partner.
        TODO: CHANGE NAME TO SOMETHING LIKE SWITCH TO CONTROL SCREEN
        """
        self._app.is_controller = self.controller_checkbox.active
        self.manager.transition.direction = "left"
        self._app.root.current = (
            "controller" if self._app.is_controller else "controlled")

    def _update_selection(self, _, username):
        """
        Update partner's label to the new username.
        :param username: The partner's username.
        """
        logging.info(f"Selected partner: {username}")
        self.partner_label.text = username

    def start_user_selector(self, connection_status):
        """
        Start the user selector
        :param connection_status: The connection status of the get users
                                  connection
        """
        if connection_status == "ready":
            self.user_selector.start(
                self._app.connection_manager.client.get_connection(
                    "get users"))

    def on_enter(self):
        """
        Start all the components and connections
        """
        self._app.connection_manager.add_connection(
            self._app.username,
            "get users",
            (True, True),
            "main",
            block=False,
            callback=self.start_user_selector)

    def on_pre_leave(self):
        """
        Close user selector and its connection.
        """
        logging.debug("starting to leave")
        self.user_selector.close()
        try:
            self._app.connection_manager.close_connection("get users")
        except Exception as e:
            logging.error("socket error while closing: " + str(e))
        logging.debug("closed connection to get users")
