"""
Streams image from a socket
"""

__author__ = "Ron Remets"

import io
import kivy.uix.image
from kivy.properties import ObjectProperty
from kivy.clock import Clock

from advanced_socket import AdvancedSocket


class ImageStreamer(kivy.uix.image.Image):
    """
    Streams image from socket
    """
    connection = ObjectProperty(None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._screen_update_event = None

    def _screen_update(self, *_):
        image_bytes = self.connection.data_received
        image_data = io.BytesIO(image_bytes)
        image_data.seek(0)
        self.texture = kivy.uix.image.CoreImage(
            image_data, ext="png").texture
        self.reload()

    def on_enter(self):
        self._screen_update_event = Clock.schedule_interval(
            self._screen_update, 0)
