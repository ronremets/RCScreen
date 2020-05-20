"""
The login screen.
"""

__author__ = "Ron Remets"

import logging

from kivy.app import App
from kivy.clock import Clock, mainthread
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.relativelayout import RelativeLayout


class LoginScreen(Screen):
    """
    The screen where the client logs to the server
    """
    username_text_input = ObjectProperty(None)
    password_text_input = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()

    @mainthread
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

    @mainthread
    def _handle_login_response(self, response):
        # TODO: handle this
        if response == "ready":
            logging.info("MAIN:logged in, creating main")
            self.app.connection_manager.add_connection(
                self.app.username,
                "main",
                (True, True),
                "main",
                block=False,
                callback=lambda main_response: self._handle_main_connect_response(main_response))
        else:
            content = RelativeLayout(size_hint=(1, 1))
            content.add_widget(Label(text=response,
                                     pos_hint={"bottom": 0.8, "left": 1},
                                     size_hint=(1, 0.8)))
            dismiss_button = Button(text=response,
                                    pos_hint={"bottom": 1, "left": 0.5},
                                    size_hind=(0.8, 0.2))
            content.add_widget(dismiss_button)
            popup = Popup(title=response, content=content)
            dismiss_button.bind(on_press=popup.dismiss)
            popup.open()

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
                callback=lambda response: self._handle_login_response(response))
        except ValueError:
            # TODO: inconsistent checking if already connecting between
            #  normal connection and connector
            logging.error(f"MAIN:Already connecting!")
        except Exception:
            logging.error(f"Unknown error while logging in", exc_info=True)
