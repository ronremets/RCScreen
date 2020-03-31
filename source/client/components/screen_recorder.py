"""
Record the screen
"""
__author__ = "Ron Remets"

import io
import logging
import threading
import time

import PIL.ImageGrab

from component import Component

DEFAULT_SCREEN_IMAGE_FORMAT = "png"


class ScreenRecorder(Component):
    """
    Record the screen
    """
    def __init__(self):
        super().__init__()
        self._name = "Screen recorder"
        # Never change screen format mid recording
        self.screen_image_format = None
        self._frame_lock = threading.Lock()
        self._frame = None

    @property
    def frame(self):
        """
        The current screen frame
        After reading the frame it will turn to None until the next
        frame is available
        :return: None if capture has not started, bytes otherwise
        """
        with self._frame_lock:
            frame = self._frame
            self._frame = None
            return frame

    def _set_frame(self, frame):
        with self._frame_lock:
            self._frame = frame

    def _update(self):
        """
        Capture current frame
        """
        frame = PIL.ImageGrab.grab()
        frame = frame.resize((1920, 1080))  # TODO: make dynamic
        frame_bytes = io.BytesIO()
        frame.save(frame_bytes, self.screen_image_format)
        frame_bytes.seek(0)
        self._set_frame(frame_bytes.read())

    def start(self, screen_image_format):
        """
        Start the screen capture
        """
        logging.info("Configuring the screen recorder")
        self.screen_image_format = screen_image_format
        self._start()
