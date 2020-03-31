"""
The signup screen.
"""

__author__ = "Ron Remets"

import logging

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty


class SignupScreen(Screen):
    """
    The screen where the client signs up to the server
    """
    signup_button = ObjectProperty(None)
    username_text_input = ObjectProperty(None)
    password_text_input = ObjectProperty(None)

    def on_signup_button_press(self):
        """
        Signup to the server.
        """
        logging.info("MAIN:signing in")
        app = App.get_running_app()
        app.username = self.username_text_input.text
        app.password = self.password_text_input.text
        app.connection_manager.add_connector(app.username,
                                             app.password,
                                             "signup")
        app.connection_manager.add_connection(
            app.username,
            "main",
            (True, True),
            "main")
        logging.info("MAIN:signed up")
        # if logged_in:
        self.manager.transition.direction = "up"
        app.root.current = "main"
