"""
Streams image from a socket
"""

__author__ = "Ron Remets"

import io

import kivy.uix.image
from kivy.clock import Clock


class StreamedImage(kivy.uix.image.Image):
    """
    Streams image from socket
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._screen_update_event = None
        self.connection = None  # TODO: replace with app.connection

    def _screen_update(self, *_):
        """
        Update the image.
        """
        image_bytes = self.connection.recv()
        image_data = io.BytesIO(image_bytes)
        image_data.seek(0)
        self.texture = kivy.uix.image.CoreImage(
            image_data, ext="png").texture
        self.reload()

    def start(self):
        """
        Start the image updating.
        """
        self._screen_update_event = Clock.schedule_interval(
            self._screen_update, 0)

    def stop(self):
        """
        Stop the streaming
        """
        self._screen_update_event.cancel()
