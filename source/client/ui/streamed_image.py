"""
An image that constantly changes trough a socket
"""
__author__ = "Ron Remets"

import io
import logging

from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty
from kivy.uix.image import Image

from communication.message import Message, MESSAGE_TYPES

DEFAULT_IMAGE_FORMAT = "png"


class StreamedImage(Image):
    """
    An image that constantly changes trough a socket
    """
    connection = ObjectProperty()
    image_format = StringProperty(DEFAULT_IMAGE_FORMAT)
    _update_frame_event = ObjectProperty(None)
    _running = BooleanProperty(False)

    def _update_frame(self, _):
        """
        Update the image to the new frame
        """
        try:
            # Try to receive a frame
            frame_message = self.connection.socket.recv(block=False)
            # If you did not receive a frame do not update the screen
            if frame_message is None:
                return
            logging.debug(
                f"FRAME:Received frame with "
                f"length: {len(frame_message.content)}")
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
        except Exception as e:  # TODO: dont be broad
            print(e)
            self.stop()
            logging.error("FRAME:An error occurred", exc_info=True)
            return

    def start(self):
        """
        Start streaming.
        """
        #  TODO:
        #   https://buildmedia.readthedocs.org/media/pdf/kivy/latest/kivy.pdf
        #   page 360
        # TODO: StreamedImage should not know about this variable
        if self._running:
            return
        logging.debug("FRAME:Starting screen update event")
        self._update_frame_event = Clock.schedule_interval(
            self._update_frame,
            0)
        self._running = True

    def stop(self):
        """
        Stop streaming.
        """
        if not self._running:
            return
        self._update_frame_event.cancel()
        self._running = False
