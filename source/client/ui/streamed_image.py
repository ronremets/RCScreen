"""
An image that constantly changes trough a socket
"""
__author__ = "Ron Remets"

import io
import logging

from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.image import Image

from communication.message import Message, MESSAGE_TYPES

DEFAULT_IMAGE_FORMAT = "png"


class StreamedImage(Image):
    """
    An image that constantly changes trough a socket
    """
    connection = ObjectProperty(None)
    image_format = StringProperty(DEFAULT_IMAGE_FORMAT)
    update_frame_event = ObjectProperty(None)

    def _update_frame(self, _):
        """
        Update the image to the new frame
        """
        frame_message = self.connection.socket.recv(block=False)
        if frame_message is None:
            return
        logging.debug(
            f"FRAME:Received frame with length: {len(frame_message.content)}")
        self.connection.socket.send(Message(MESSAGE_TYPES["controller"],
                                    "Message received"))

        frame_data = io.BytesIO(frame_message.content)
        frame_data.seek(0)

        logging.debug("FRAME:Creating core image")
        self.texture = CoreImage(frame_data,
                                 ext=self.image_format).texture
        logging.debug("FRAME:Reloading screen")
        self.reload()
        logging.debug("FRAME:SCREEN UPDATED")

    def start(self):
        """
        Start streaming.
        """
        # TODO: https://buildmedia.readthedocs.org/media/pdf/kivy/latest/kivy.pdf
        #  page 360
        logging.debug("FRAME:Starting screen update event")
        self.update_frame_event = Clock.schedule_interval(self._update_frame,
                                                          0)

    def close(self):
        """
        Stop streaming.
        """
        if self.update_frame_event is not None:
            self.update_frame_event.cancel()
