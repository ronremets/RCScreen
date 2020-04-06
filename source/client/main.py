"""
This is the entry point of the client's application.
"""
__author__ = "Ron Remets"

import logging
import pkg_resources.py2_warn

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import (BooleanProperty,
                             NumericProperty,
                             ObjectProperty,
                             StringProperty)

from connection_manager import ConnectionManager

import ui
# Tree("D:\\Programming\\Python\\RCScreen\\source\\client\\components"),
# Tree("D:\\Programming\\Python\\RCScreen\\source\\client\\ui\\screen", prefix="screen"),
# Tree("D:\\Programming\\Python\\RCScreen\\source\\client\\ui\\popup", prefix="popup"),
# Tree("D:\\Programming\\Python\\RCScreen\\source\\client\\ui", prefix="ui", excludes=["screen", "popup"]),
# Tree("D:\\Programming\\Python\\RCScreen\\source\\client", excludes=["components", "ui"]),
# Tree("D:\\Programming\\Python\\RCScreen\\source\\communication", prefix="communication"),
# Tree("C:\\Program Files\\Python37\\Lib\\site-packages\\lz4", prefix='lz4'),
# Tree("C:\\Program Files\\Python37\\Lib\\site-packages\\PIL", prefix="PIL"),
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

    def build(self):
        """
        Builds the application.
        :return: The application object.
        """
        return Builder.load_file("RCScreen.kv")


if __name__ == '__main__':
    RCScreenApp().run()
