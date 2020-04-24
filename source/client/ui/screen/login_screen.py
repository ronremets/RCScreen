"""
The login screen.
"""

__author__ = "Ron Remets"

import logging

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty


class LoginScreen(Screen):
    """
    The screen where the client logs to the server
    """
    username_text_input = ObjectProperty(None)
    password_text_input = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()

    def _handle_main_connect_response(self, response):
        # TODO: handle this
        if response == "bad token":
            pass
        elif response == "server crash":
            pass
        elif response == "other":
            pass
        logging.info("MAIN:Created main, switching to main menu")
        # if logged_in:
        self.manager.transition.direction = "up"
        self.app.root.current = "main"

    def _handle_login_response(self, response):
        # TODO: handle this
        if response == "Username or password are wrong":
            logging.error("Username or password are wrong")
        elif response == "User already connected":
            logging.error("User already connected")
        elif response == "Connection method does not exists":
            logging.error("Connection method does not exists")
        elif response == "Unknown server Error":
            logging.error("Unknown server Error")
        elif response == "ready":
            logging.info("MAIN:logged in, creating main")
            self.app.connection_manager.add_connection(
                self.app.username,
                "main",
                (True, True),
                "main",
                block=False,
                callback=lambda main_response: Clock.schedule_once(lambda _: self._handle_main_connect_response(main_response)))
            return
        # close connector

    def login(self):
        """
        login to the server.
        """
        logging.info("MAIN:logging in")
        self.app.username = self.username_text_input.text
        self.app.password = self.password_text_input.text
        try:
            self.app.connection_manager.add_connector(
                self.app.username,
                self.app.password,
                "login",
                callback=lambda response: Clock.schedule_once(lambda _: self._handle_login_response(response)))
        except ValueError:
            # TODO: inconsistent checking if already connecting between
            #  normal connection and connector
            logging.error(f"MAIN:Already connecting!")
