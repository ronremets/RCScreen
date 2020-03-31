"""
This is the entry point of the client's application.
"""
__author__ = "Ron Remets"

import logging

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import BooleanProperty, ObjectProperty, StringProperty

from connection_manager import ConnectionManager

import ui

SERVER_ADDRESS = ("127.0.0.1", 2125)
logging.basicConfig(level=logging.DEBUG)

DEFAULT_SCREEN_IMAGE_FORMAT = "png"


class RCScreenApp(App):
    """
    Responsible for the whole client's application.
    """
    screen_image_format = StringProperty(DEFAULT_SCREEN_IMAGE_FORMAT)
    username = StringProperty("")
    password = StringProperty("")
    is_controller = BooleanProperty(False)
    partner = StringProperty("")
    connection_manager = ObjectProperty(ConnectionManager())

    def on_start(self):
        """
        Start connection_manager
        """
        self.connection_manager.start(SERVER_ADDRESS)

    def on_stop(self):
        """
        Close connection_manager
        """
        self.connection_manager.close()

    def build(self):
        """
        Builds the application.
        :return: The application object.
        """
        return Builder.load_file("RCScreen.kv")


if __name__ == '__main__':
    RCScreenApp().run()
