"""
This is the entry point of the client's application.
"""
__author__ = "Ron Remets"


from kivy.app import App
from kivy.properties import (BooleanProperty,
                             NumericProperty,
                             ObjectProperty,
                             StringProperty,
                             ListProperty)
# this import is required by kivy
# noinspection PyUnresolvedReferences
import ui
from connection_manager import ConnectionManager

DEFAULT_SCREEN_IMAGE_FORMAT = "png"


class RCScreenApp(App):
    """
    Responsible for the whole client's application.
    """
    screen_image_format = StringProperty(DEFAULT_SCREEN_IMAGE_FORMAT)
    username = StringProperty("")
    password = StringProperty("")
    # TODO: can connect_screen handle this?
    is_controller = BooleanProperty(True)
    # TODO: can connect_screen handle this?
    partner = StringProperty("")
    connection_manager = ObjectProperty(ConnectionManager())
    x_sensitivity = NumericProperty(10, min=0)
    y_sensitivity = NumericProperty(10, min=0)
    screen_size = ListProperty()
    other_screen_width = NumericProperty(0)
    other_screen_height = NumericProperty(0)

    def on_stop(self):
        """
        Close connection_manager
        """
        if self.connection_manager.running:
            self.connection_manager.close()
