"""
Stores information about the mouse
"""
__author__ = "Ron Remets"

import threading


class Mouse(object):
    """
    Stores information about the mouse
    """
    def __init__(self):
        self._x_lock = threading.Lock()
        self._y_lock = threading.Lock()
        self._left_button_lock = threading.Lock()
        self._right_button_lock = threading.Lock()
        self._x_sensitivity_lock = threading.Lock()
        self._y_sensitivity_lock = threading.Lock()
        self.x = 0
        self.y = 0
        self.left_button = "released"
        self.right_button = "released"
        self.x_sensitivity = 10
        self.y_sensitivity = 10

    @property
    def x(self):
        with self._x_lock:
            return self._x

    @x.setter
    def x(self, value):
        with self._x_lock:
            self._x = value

    @property
    def y(self):
        with self._y_lock:
            return self._y

    @y.setter
    def y(self, value):
        with self._y_lock:
            self._y = value

    @property
    def left_button(self):
        with self._left_button_lock:
            return self._left_button

    @left_button.setter
    def left_button(self, value):
        with self._left_button_lock:
            self._left_button = value

    @property
    def right_button(self):
        with self._right_button_lock:
            return self._right_button

    @right_button.setter
    def right_button(self, value):
        with self._right_button_lock:
            self._right_button = value

    @property
    def x_sensitivity(self):
        with self._x_sensitivity_lock:
            return self._x_sensitivity

    @x_sensitivity.setter
    def x_sensitivity(self, value):
        with self._x_sensitivity_lock:
            self._x_sensitivity = value

    @property
    def y_sensitivity(self):
        with self._y_sensitivity_lock:
            return self._y_sensitivity

    @y_sensitivity.setter
    def y_sensitivity(self, value):
        with self._y_sensitivity_lock:
            self._y_sensitivity = value

    def __repr__(self):
        return f"{self.x}, {self.y}, {self.left_button}, {self.right_button}"
