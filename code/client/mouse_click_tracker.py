"""
Tracks the state of the mouse buttons
"""
__author__ = "Ron Remets"

import logging
import threading

from tracker import Tracker


class MouseClickTracker(Tracker):
    """
    Tracks the state of the mouse buttons
    """
    def __init__(self):
        super().__init__("Mouse click tracker")
        self._buttons_state_lock = threading.Lock()
        self._set_buttons_state(None)

    @property
    def buttons_state(self):
        """
        :return: A dict with the state of the mouse buttons
        """
        with self._buttons_state_lock:
            return self._buttons_state

    def _set_buttons_state(self, value):
        with self._buttons_state_lock:
            self._buttons_state = value

    def _update(self):
        """
        Get the mouse buttons state and update buttons_state
        """
        raise NotImplementedError()