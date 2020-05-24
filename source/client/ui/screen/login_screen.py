"""
The login screen.
"""

__author__ = "Ron Remets"

import logging

from kivy.app import App
from kivy.clock import mainthread
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty

from popup.error_popup import ErrorPopup


class LoginScreen(Screen):
    """
    The screen where the client logs to the server
    """
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
            self.app.root.current = "connect"
        else:
            self._display_error_popup(response)

    @mainthread
    def _handle_login_response(self, response):
        if response == "ready":
            logging.info("MAIN:logged in, creating main")
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
                callback=lambda response:
                    self._handle_login_response(response))
        except ValueError:
            # TODO: inconsistent checking if already connecting between
            #  normal connection and connector
            logging.error(f"MAIN:Already connecting!")
        except Exception as e:
            print(e)
            logging.error(f"Unknown error while logging in", exc_info=True)
