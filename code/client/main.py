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

from client.connection_manager import ConnectionManager

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
    partner = StringProperty()
    connection_manager = ObjectProperty(ConnectionManager())

    def on_start(self):
        """
        Start connection_manager
        """
        self.connection_manager.start(SERVER_ADDRESS)

    def build(self):
        """
        Builds the application.
        :return: The application object.
        """
        return Builder.load_file("RCScreen.kv")


if __name__ == '__main__':
    RCScreenApp().run()
