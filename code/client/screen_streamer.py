"""
Streams the screen through a socket
"""
__author__ = "Ron Remets"

import logging

from communication.message import Message, MESSAGE_TYPES
from component import Component
from screen_recorder import ScreenRecorder


class ScreenStreamer(Component):
    """
    Streams the screen through a socket
    """
    def __init__(self):
        super().__init__()
        self._name = "Screen streamer"
        self._connection = None
        self._screen_recorder = ScreenRecorder()

    def _setup(self):
        """
        setup the connection
        """
        while not self._connection.connected:
            pass
        logging.info("Screen connected")

    def _update(self):
        """
        Send the next frame
        """
        frame = self._screen_recorder.frame
        if frame is not None:
            self._connection.socket.send(Message(
                MESSAGE_TYPES["controlled"],
                frame))
            # Make sure server is ready to receive another frame
            self._connection.socket.recv()

    def start(self, connection, screen_image_format):
        """
        Start the recording and streaming
        :param connection: The connection to use to stream
        :param screen_image_format: The format to use when streaming
        """
        self._connection = connection
        # TODO: add timeout for socket
        self._screen_recorder.start(screen_image_format)
        self._start()

    def close(self, timeout=None):
        """
        Close all threads and stops streaming
        TODO: NOTE: DOES NOT CLOSE THE CONNECTION
        :param timeout: The time in seconds to wait before closing
        """
        # TODO: keep timeout time between all closing!!!
        super().close(timeout)
        if self._screen_recorder is not None:
            self._screen_recorder.close(timeout)
