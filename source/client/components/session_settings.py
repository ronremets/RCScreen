"""
Gets and sets the settings between clients
"""
__author__ = "Ron Remets"

import queue

from kivy.clock import Clock, mainthread
from kivy.app import App

from component import Component


class SessionSettings(Component):
    """
    Gets and sets the settings between clients
    """
    def __init__(self):
        super().__init__()
        self._name = "session settings"
        self._app = None
        self._connection = None
        # Queue of messages with updates
        self.settings_updates = queue.Queue()

    @mainthread
    def _change_other_screen(self, width, height):
        """
        Change the size of the other screen setting.
        :param width: The width of the other screen
        :param height: The height of the other screen
        """
        self._app.other_screen_width = width
        self._app.other_screen_height = height

    def _handle_settings(self, setting):
        name, value = setting.split(":")
        if name == "other screen size":
            width, height = value.split(", ")
            self._change_other_screen(width, height)
        else:
            # TODO: what other settings to add?
            pass

    def _update(self):
        message = self._connection.socket.recv(block=False)
        if message is not None:
            self._handle_settings(message.get_content_as_text())
        try:
            update = self.settings_updates.get(block=False)
        except queue.Empty:
            pass
        else:
            self._connection.socket.send(update)

    def start(self, connection):
        """
        Start the controller
        :param connection: The connection to get the info from.
        """
        self._app = App.get_running_app()
        self._connection = connection
        self._start()
