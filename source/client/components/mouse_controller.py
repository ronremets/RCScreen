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
from streamed_controller import CONTROLLER_INSTRUCTIONS

DEFAULT_CLICK_DELAY = 0.1
DEFAULT_SENSITIVITY = 10


class MouseController(Component):
    """
    Controls the mouse using info from a socket
    """
    def __init__(self):
        super().__init__()
        self._connection = None
        self._click_delay_lock = threading.Lock()
        self._sensitivity_lock = threading.Lock()
        self.click_delay = DEFAULT_CLICK_DELAY
        self.sensitivity = DEFAULT_SENSITIVITY

    @property
    def click_delay(self):
        """
        THREAD SAFE
        The delay between pressing a button and releasing it when
        clicking the mouse.
        :return: The seconds in float.
        """
        with self._click_delay_lock:
            return self._click_delay

    @click_delay.setter
    def click_delay(self, value):
        """
        THEAD SAFE
        Set the delay between pressing a button and releasing it when
        clicking the mouse.
        :param value: The seconds in float.
        """
        with self._click_delay_lock:
            self._click_delay = value

    @property
    def sensitivity(self):
        """
        THREAD SAFE
        The amount of pixels to move each mouse move.
        :return: The pixels as an int.
        """
        with self._sensitivity_lock:
            return self._sensitivity

    @sensitivity.setter
    def sensitivity(self, sensitivity):
        """
        THEAD SAFE
        The amount of pixels to move each mouse move.
        :param sensitivity: The pixels as an int.
        """
        with self._sensitivity_lock:
            self._sensitivity = sensitivity

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
        instruction = string
        if instruction not in CONTROLLER_INSTRUCTIONS.values():
            raise ValueError("Instruction does not exists")
        return {"instruction": instruction}

    def handle_mouse_instruction(self, instruction):
        """
        Move the mouse according to the instruction
        :param instruction: The instruction as a string
        """
        x, y = win32gui.GetCursorPos()
        if instruction == CONTROLLER_INSTRUCTIONS["move left"]:
            win32api.SetCursorPos((x - self.sensitivity, y))
        elif instruction == CONTROLLER_INSTRUCTIONS["move right"]:
            win32api.SetCursorPos((x + self.sensitivity, y))
        elif instruction == CONTROLLER_INSTRUCTIONS["move up"]:
            win32api.SetCursorPos((x, y - self.sensitivity))
        elif instruction == CONTROLLER_INSTRUCTIONS["move down"]:
            win32api.SetCursorPos((x, y + self.sensitivity))
        elif instruction == CONTROLLER_INSTRUCTIONS["click left"]:
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
            time.sleep(self.click_delay)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)
        elif instruction == CONTROLLER_INSTRUCTIONS["click right"]:
            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, x, y, 0, 0)
            time.sleep(self.click_delay)
            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, x, y, 0, 0)

    def _update(self):
        message = self._connection.socket.recv(block=False)
        if message is not None:
            parameters = self._parse_mouse_instruction(
                message.get_content_as_text())
            self.handle_mouse_instruction(parameters["instruction"])

    def start(self, connection):
        """
        Start the controller
        :param connection: The connection to get the info from.
        """
        self._connection = connection
        self._start()
