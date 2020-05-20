"""
Controls the mouse using info from a socket
"""
__author__ = "Ron Remets"

import threading
import time
import win32api
import win32con
import win32gui

from components.component import Component

DEFAULT_CLICK_DELAY = 0.1


class MouseController(Component):
    """
    Controls the mouse using info from a socket
    """
    def __init__(self):
        super().__init__()
        self._name = "Mouse controller"
        self._connection = None
        self._click_delay_lock = threading.Lock()
        self.click_delay = DEFAULT_CLICK_DELAY

    @property
    def click_delay(self):
        with self._click_delay_lock:
            return self._click_delay

    @click_delay.setter
    def click_delay(self, value):
        with self._click_delay_lock:
            self._click_delay = value

    @staticmethod
    def _parse_mouse_instruction(string):
        """
        Parse a string containing the parameters of the mouse update
        info and return them as a dict.
        :param string: The string containing the parameters of the
                       instruction.
        :return: A dict with the parameters of the instruction.
        :raise ValueError: If instruction does not exits
        """
        action, button, pos = string.split(" ")
        return {"action": action, "button": button, "pos": pos.split(",")}

    def _handle_mouse_instruction(self, parameters):
        """
        Move the mouse according to the instruction
        :param parameters: The parameters as a dict
        """
        x, y = parameters["pos"]
        x, y = int(x), int(y)
        if parameters["action"] == "move":
            win32api.SetCursorPos((x, y))
        elif parameters["action"] == "press":
            if parameters["button"] == "left":
                button_event = win32con.MOUSEEVENTF_LEFTDOWN
            else:
                button_event = win32con.MOUSEEVENTF_RIGHTDOWN
            win32api.mouse_event(button_event, x, y, 0, 0)
        elif parameters["action"] == "release":
            if parameters["button"] == "left":
                button_event = win32con.MOUSEEVENTF_LEFTUP
            else:
                button_event = win32con.MOUSEEVENTF_RIGHTUP
            win32api.mouse_event(button_event, x, y, 0, 0)
        elif parameters["action"] == "click":
            if parameters["button"] == "left":
                button_event = win32con.MOUSEEVENTF_LEFTDOWN
            else:
                button_event = win32con.MOUSEEVENTF_RIGHTDOWN
            win32api.mouse_event(button_event, x, y, 0, 0)
            time.sleep(self.click_delay)
            if parameters["button"] == "left":
                button_event = win32con.MOUSEEVENTF_LEFTUP
            else:
                button_event = win32con.MOUSEEVENTF_RIGHTUP
            win32api.mouse_event(button_event, x, y, 0, 0)

    def _update(self):
        message = self._connection.socket.recv(block=False)
        if message is not None:
            parameters = self._parse_mouse_instruction(
                message.get_content_as_text())
            self._handle_mouse_instruction(parameters)

    def start(self, connection):
        """
        Start the controller
        :param connection: The connection to get the info from.
        """
        self._connection = connection
        self._start()
