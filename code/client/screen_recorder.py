"""
Record the screen
TODO: maybe subclass is thread? maybe no subclass?
"""

__author__ = "Ron Remets"

import io
import logging
import threading

import PIL.ImageGrab

from tracker import Tracker

DEFAULT_SCREEN_FORMAT = "png"


class ScreenRecorder(Tracker):
    """
    Record the screen
    """

    def __init__(self):
        super().__init__("Screen recorder")
        # Never change screen format mid recording
        self.screen_image_format = DEFAULT_SCREEN_FORMAT
        self._frame_lock = threading.Lock()
        with self._frame_lock:
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
        frame = frame.resize((720, 480))
        frame_bytes = io.BytesIO()
        frame.save(frame_bytes, self.screen_image_format)
        frame_bytes.seek(0)
        self._set_frame(frame_bytes.read())

    def start(self):
        """
        Start the screen capture
        """
        logging.info("Configuring the screen recorder")
        super().start()
