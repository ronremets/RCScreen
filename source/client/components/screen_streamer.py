"""
Streams the screen through a socket
"""
__author__ = "Ron Remets"

import logging

from communication.message import Message, MESSAGE_TYPES
from components.component import Component
from components.screen_recorder import ScreenRecorder


class ScreenStreamer(Component):
    """
    Streams the screen through a socket
    """
    def __init__(self):
        super().__init__()
        self._name = "Screen streamer"
        self._connection = None
        self._can_send_frame = True
        self.screen_recorder = ScreenRecorder()  # TODO: Lock?

    def _send_frame(self):
        """
        Send a frame to through the socket
        """
        frame = self.screen_recorder.frame
        if frame is not None:
            self._connection.socket.send(Message(
                MESSAGE_TYPES["controlled"],
                frame))
            self._can_send_frame = False

    def _check_if_can_send_frame(self):
        """
        Check if the connection is ready to receive another frame
        """
        response = self._connection.socket.recv(block=False)
        if response is not None:
            self._can_send_frame = True

    def _update(self):
        """
        Send the next frame
        """
        if self._can_send_frame:
            self._send_frame()
        else:
            self._check_if_can_send_frame()

    def start(self, connection):
        """
        Start the recording and streaming
        :param connection: The connection to use to stream
        """
        self._connection = connection
        self._can_send_frame = True
        self.screen_recorder.start()
        self._start()

    def close(self, timeout=None):
        """
        Close all threads and stops streaming
        TODO: NOTE: DOES NOT CLOSE THE CONNECTION
        :param timeout: The time in seconds to wait before closing
        """
        # TODO: keep timeout time between all closing!!!
        super().close(timeout)
        if self.screen_recorder is not None:
            self.screen_recorder.close(timeout)
