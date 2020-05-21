"""
Track the state of the keyboard
"""
__author__ = "Ron Remets"

import logging

from kivy.core.window import Window
from kivy.properties import ObjectProperty, BooleanProperty
from kivy.uix.widget import Widget

from communication.message import Message, MESSAGE_TYPES


class KeyboardTracker(Widget):
    """
    Send the keyboard state through a socket
    """
    connection = ObjectProperty()
    is_tracking = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._keyboard = None

    def _on_keyboard_key_down(self, _, keycode, _2, modifiers):
        if not self.is_tracking:
            return False
        self.connection.socket.send(Message(
            MESSAGE_TYPES["controller"],
            f"{keycode[1]}, press"))
        logging.debug(f"KEYBOARD:The key, {keycode}, has been pressed\n"
                      f"modifiers are {modifiers!r}")

        # Return True to accept the key. Otherwise, it will be used by
        # the system.
        return True

    def _on_keyboard_key_up(self, _, keycode):
        """
        When a key is pressed, send its keycode to the server.
        :param keycode: The string representation of the key.
        """
        if not self.is_tracking:
            return False
        self.connection.socket.send(Message(
            MESSAGE_TYPES["controller"],
            f"{keycode[1]}, release"))
        logging.debug(f"KEYBOARD:The key, {keycode}, has been released")
        return True

    def _on_keyboard_close(self):
        logging.debug('KEYBOARD:Keyboard closed!')
        self._keyboard.unbind(on_key_down=self._on_keyboard_key_down,
                              on_key_up=self._on_keyboard_key_up)
        self._keyboard = None

    def show_keyboard(self):
        """
        Show the keyboard and start sending its state.
        Make sure that connection is set before showing the keyboard
        """
        if self._keyboard is not None:
            return
        logging.debug("KEYBOARD:showing keyboard")
        self._keyboard = Window.request_keyboard(
            self._on_keyboard_close, self, 'text')
        self._keyboard.bind(on_key_down=self._on_keyboard_key_down,
                            on_key_up=self._on_keyboard_key_up)

    def hide_keyboard(self):
        """
        Hide and close the keyboard.
        """
        if self._keyboard is not None:
            self.keyboard.release()
