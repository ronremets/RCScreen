"""
Record the screen
"""
__author__ = "Ron Remets"

import io
import threading

import PIL.ImageGrab

from components.component import Component

DEFAULT_IMAGE_FORMAT = "png"
DEFAULT_RESOLUTION = (1920, 1080)


class ScreenRecorder(Component):
    """
    Record the screen
    """
    def __init__(self):
        super().__init__()
        self._name = "Screen recorder"
        self._frame_lock = threading.Lock()
        self._image_format_lock = threading.Lock()
        self._resolution_lock = threading.Lock()
        self._frame = None
        self.image_format = DEFAULT_IMAGE_FORMAT
        self.resolution = DEFAULT_RESOLUTION

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

    @property
    def image_format(self):
        """
        THREAD SAFE
        The image_format of the screen capture.
        :return: The image_format as a string.
        """
        with self._image_format_lock:
            return self._image_format

    @image_format.setter
    def image_format(self, image_format):
        """
        THEAD SAFE
        Set the image_format of the screen capture.
        :param image_format: The image_format as a string.
        """
        with self._image_format_lock:
            self._image_format = image_format

    @property
    def resolution(self):
        """
        THREAD SAFE
        The resolution of the screen capture.
        :return: The resolution as a tuple (pixels, pixels)
        """
        with self._resolution_lock:
            return self._resolution

    @resolution.setter
    def resolution(self, resolution):
        """
        THEAD SAFE
        Set the resolution of the screen capture.
        :param resolution: The image_format as a tuple (pixels, pixels).
        """
        with self._resolution_lock:
            self._resolution = resolution

    def _update(self):
        """
        Capture current frame
        """
        frame = PIL.ImageGrab.grab()
        frame = frame.resize(self.resolution)  # TODO: make dynamic
        frame_bytes = io.BytesIO()
        frame.save(frame_bytes, self.image_format)
        frame_bytes.seek(0)
        self._set_frame(frame_bytes.read())

    def start(self):
        """
        Start the screen capture
        """
        self._start()
