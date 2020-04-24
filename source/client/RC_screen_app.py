"""
This is the entry point of the client's application.
"""
__author__ = "Ron Remets"

import logging

from kivy.app import App
from kivy.properties import (BooleanProperty,
                             NumericProperty,
                             ObjectProperty,
                             StringProperty)

from connection_manager import ConnectionManager

import ui

SERVER_ADDRESS = ("127.0.0.1", 2125)
DEFAULT_SCREEN_IMAGE_FORMAT = "png"


class RCScreenApp(App):
    """
    Responsible for the whole client's application.
    """
    screen_image_format = StringProperty(DEFAULT_SCREEN_IMAGE_FORMAT)
    username = StringProperty("")
    password = StringProperty("")
    is_controller = BooleanProperty(False) # TODO: can connect_screen handle this?
    partner = StringProperty("") # TODO: can connect_screen handle this?
    connection_manager = ObjectProperty(ConnectionManager())
    x_sensitivity = NumericProperty(10, min=0)
    y_sensitivity = NumericProperty(10, min=0)

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
