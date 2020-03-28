"""
Send the keyboard state through a socket
"""
__author__ = "Ron Remets"

from kivy.core.window import Window
from kivy.properties import ObjectProperty
from kivy.uix.widget import Widget

from communication.message import Message, MESSAGE_TYPES


class KeyboardStreamer(Widget):
    """
    Send the keyboard state through a socket
    """
    start_button = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._keyboard = None
        self._connection = None

    def _on_keyboard_key_down(self, keyboard, keycode, text, modifiers):
        # self._connection.socket.send(Message(
        #    MESSAGE_TYPES["controller"],
        #    keycode))
        print('The key', keycode, 'has been pressed')
        print(' - text is %r' % text)
        print(' - modifiers are %r' % modifiers)

        # Keycode is composed of an integer + a string
        # If we hit escape, release the keyboard
        if keycode[1] == 'escape':
            self.hide_keyboard()

        # Return True to accept the key. Otherwise, it will be used by
        # the system.
        return True

    def _on_keyboard_key_up(self, keyboard, keycode, text, modifiers):
        """
        When a key is pressed, send its keycode to the server
        :param keyboard: The keyboard of the key.
        :param keycode: The string representation of the key.
        :param text: TODO: ?
        :param modifiers: TODO: ?'
        :return: True in order to stop the key release from being
                 registered elsewhere in the operating system.
        """
        #self._connection.socket.send(Message(
        #    MESSAGE_TYPES["controller"],
        #    keycode))
        print('The key', keycode, 'has been released')
        print(' - text is %r' % text)
        print(' - modifiers are %r' % modifiers)
        return True

    def _on_keyboard_close(self):
        print('My keyboard have been closed!')
        self._keyboard.unbind(on_key_down=self._on_keyboard_down,
                              on_key_up=self._on_keyboard_key_up)
        self._keyboard = None

    def show_keyboard(self, connection):
        """
        Show the keyboard and start sending its state.
        :param connection: The connection to use to send the keys
        """
        self._connection = connection
        self._keyboard = Window.request_keyboard(
            self._on_keyboard_close, self, 'text')
        if self._keyboard.widget is None:
            raise ValueError("No keyboard")
        self._keyboard.bind(on_key_down=self._on_keyboard_key_down,
                            on_key_up=self._on_keyboard_key_up)

    def hide_keyboard(self):
        """
        Hide and close the keyboard.
        """
        self.keyboard.release()
