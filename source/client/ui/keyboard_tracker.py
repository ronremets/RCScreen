"""
Track the state of the keyboard
"""
__author__ = "Ron Remets"

import logging

from kivy.core.window import Window
from kivy.properties import ObjectProperty
from kivy.uix.widget import Widget

from communication.message import Message, MESSAGE_TYPES


class KeyboardTracker(Widget):
    """
    Send the keyboard state through a socket
    """
    start_button = ObjectProperty()
    connection = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._keyboard = None

    def _on_keyboard_key_down(self, keyboard, keycode, text, modifiers):
        #self.connection.socket.send(Message(
        #    MESSAGE_TYPES["controller"],
        #    f"{keycode} pressed"))
        logging.debug(f"The key, {keycode}, has been pressed")
        logging.debug(f" - text is {text!r}")
        logging.debug(f" - modifiers are {modifiers!r}")

        # Keycode is composed of an integer + a string
        # If we hit escape, release the keyboard
        if keycode[1] == 'escape':
            self.hide_keyboard()

        # Return True to accept the key. Otherwise, it will be used by
        # the system.
        return True

    def _on_keyboard_key_up(self, keyboard, keycode):
        """
        When a key is pressed, send its keycode to the server
        :param keyboard: The keyboard of the key.
        :param keycode: The string representation of the key.
        """
        #self.connection.socket.send(Message(
        #    MESSAGE_TYPES["controller"],
        #    f"{keycode} released"))
        logging.debug(f"The key, {keycode}, has been released")
        return True

    def _on_keyboard_close(self):
        logging.debug('My keyboard have been closed!')
        self._keyboard.unbind(on_key_down=self._on_keyboard_key_down,
                              on_key_up=self._on_keyboard_key_up)
        self._keyboard = None

    def show_keyboard(self):
        """
        Show the keyboard and start sending its state.
        Make sure that connection is set before showing the keyboard
        """
        self._keyboard = Window.request_keyboard(
            self._on_keyboard_close, self, 'text')
        #if self._keyboard.widget is None:
        #    raise ValueError("No keyboard")
        self._keyboard.bind(on_key_down=self._on_keyboard_key_down,
                            on_key_up=self._on_keyboard_key_up)

    def hide_keyboard(self):
        """
        Hide and close the keyboard.
        """
        self.keyboard.release()
