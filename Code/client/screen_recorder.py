"""
Record the screen
"""

__author__ = "Ron Remets"

import io
import threading

import PIL.ImageGrab
#from mss import mss


class ScreenRecorder(object):
    """
    Record the screen
    """

    def __init__(self):
        self._capture_frame_thread = None
        self._frame_lock = threading.Lock()
        self._running_lock = threading.Lock()
        self._set_frame(None)
        self._set_running(False)

    @property
    def running(self):
        with self._running_lock:
            return self.__running

    def _set_running(self, value):
        with self._running_lock:
            self.__running = value

    @property
    def frame(self):
        with self._frame_lock:
            return self.__frame

    def _set_frame(self, frame):
        with self._frame_lock:
            self.__frame = frame

    def _capture_frame(self):
        """
        Capture current frame
        """
        while self.running:
            frame = PIL.ImageGrab.grab()
            # print(frame.size)
            #frame = frame.resize((240, 140))
            #with mss() as screen_shooter:
            #    frame = screen_shooter.grab(screen_shooter.monitors[0])
            frame_bytes = io.BytesIO()
            frame.save(frame_bytes, "png")
            frame_bytes.seek(0)
            self._set_frame(frame_bytes.read())
            #self._set_frame(PIL.Image.frombytes(
            #   'RGB',
            #   frame.size,
            #   frame.bgra,
            #   'raw',
            #   'BGRX').tobytes())

    def start(self):
        """
        Start the screen capture
        """
        self._capture_frame_thread = threading.Thread(
            target=self._capture_frame)
        self._set_running(True)
        self._capture_frame_thread.start()

    def close(self, block=True):
        """
        Close the capture
        :param block: If True, Wait for threads to close
        """
        self._set_running(False)
        if block:
            if self._capture_frame_thread is not None:
                self._capture_frame_thread.join()
