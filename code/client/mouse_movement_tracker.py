"""
A class for tracking mouse movement
"""

__author__ = "Ron Remets"


import logging
import threading
import win32gui

from tracker import Tracker


class MouseMovementTracker(Tracker):
    """
    Tracks the mouse movement in a thread safe way
    """
    def __init__(self):
        super().__init__("Mouse movement tracker")
        self._current_position_lock = threading.Lock()
        self._set_current_position(None)

    @property
    def current_position(self):
        """
        The current position of the mouse
        :return: None if capture has not started, (x, y) otherwise
        """
        with self._current_position_lock:
            return self._current_position

    def _set_current_position(self, point):
        """
        Sets the current position of the mouse
        :param point: (x, y)
        """
        with self._current_position_lock:
            self._current_position = point

    def _update(self):
        """
        Get the current position of the mouse and update
        current_position
        """
        point = win32gui.GetCursorPos()
        self._set_current_position(point)
