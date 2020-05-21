"""
The signup screen.
"""

__author__ = "Ron Remets"

import logging

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty
from kivy.clock import mainthread

from popup.error_popup import ErrorPopup


class SignupScreen(Screen):
    """
    The screen where the client signs up to the server
    """
    signup_button = ObjectProperty(None)
    username_text_input = ObjectProperty(None)
    password_text_input = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()

    @staticmethod
    def _display_error_popup(content):
        """
        TODO: dont make it static, make it a class
        Display an error popup with a message
        :param content: The content to display.
        """
        error_popup = ErrorPopup()
        error_popup.content_label.text = content
        error_popup.open()

    @mainthread
    def _handle_main_connect_response(self, response):
        if response == "ready":
            logging.info("MAIN:Created main, switching to main menu")
            self.manager.transition.direction = "up"
            self.app.root.current = "main"
        else:
            self._display_error_popup(response)

    @mainthread
    def _handle_signup_response(self, response):
        if response == "ready":
            logging.info("MAIN:Signed up, creating main")
            self.app.connection_manager.add_connection(
                self.app.username,
                "main",
                (True, True),
                "main",
                block=False,
                callback=lambda main_response:
                self._handle_main_connect_response(main_response))
        else:
            self._display_error_popup(response)

    def on_signup_button_press(self):
        """
        Signup to the server.
        """
        logging.info("MAIN:signing in")
        self.app = App.get_running_app()
        self.app.username = self.username_text_input.text
        self.app.password = self.password_text_input.text
        try:
            self.app.connection_manager.add_connector(
                self.app.username,
                self.app.password,
                "signup",
                callback=lambda response:
                self._handle_signup_response(response))
        except ValueError:
            # TODO: inconsistent checking if already connecting between
            #  normal connection and connector
            logging.error(f"MAIN:Already connecting!")
        except Exception as e:
            print(e)
            logging.error(f"Unknown error while logging in", exc_info=True)
