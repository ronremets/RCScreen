"""
The login screen.
"""

__author__ = "Ron Remets"

import logging

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty


class LoginScreen(Screen):
    """
    The screen where the client logs to the server
    """
    login_button = ObjectProperty(None)
    username_text_input = ObjectProperty(None)
    password_text_input = ObjectProperty(None)

    def on_login_button_press(self):
        """
        login to the server.
        """
        print("MAIN:logging in")
        app = App.get_running_app()
        app.username = self.username_text_input.text
        app.password = self.password_text_input.text
        app.connection_manager.add_connector(app.username,
                                             app.password,
                                             "login")
        app.connection_manager.add_connection("main",
                                              (True, True),
                                              "main")
        logging.info("MAIN:logged in")
        # if logged_in:
        self.manager.transition.direction = "up"
        app.root.current = "main"
