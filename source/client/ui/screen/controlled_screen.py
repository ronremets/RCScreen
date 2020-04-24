"""
The controlled screen.
"""

__author__ = "Ron Remets"

import threading
import time
import logging

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty

from components.mouse_controller import MouseController
from components.screen_streamer import ScreenStreamer
from communication.message import Message, MESSAGE_TYPES


class ControlledScreen(Screen):
    """
    The screen where the client is controlled by another client.
    """
    mouse_controller = ObjectProperty(MouseController())
    screen_streamer = ObjectProperty(ScreenStreamer())

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._app = App.get_running_app()

    def _start_mouse_controller(self, connection_status):
        """
        Start the mouse_controller.
        :param connection_status: The connection status of the
                                  connection used to by the mouse
        """
        self.mouse_controller.start(
            self._app.connection_manager.connections["mouse tracker"])

    def _start_screen_streamer(self, connection_status):
        """
        Start the screen streamer.
        :param connection_status: The connection status of the
                                  connection used to stream
        """
        #self.screen_streamer.screen_recorder.image_format = self._app.screen_image_format
        self.screen_streamer.start(
            self._app.connection_manager.connections["screen recorder"])

    def on_enter(self, *args):
        """
        When this screen starts, start recording the screen.
        """
        logging.info("Creating mouse tracker connection")
        self._app.connection_manager.add_connection(
            self._app.username,
            "mouse tracker",
            (True, True),
            "mouse - receiver",
            block=False,
            callback=self._start_mouse_controller,
            only_recv=True)
        logging.info("Creating screen recorder connection")
        self._app.connection_manager.add_connection(
            self._app.username,
            "screen recorder",
            (True, False),
            "frame - sender",
            block=False,
            callback=self._start_screen_streamer)

    def on_leave(self, *args):
        """
        When this screen stops, wait for screen to stop.
        """
        # TODO: what happens if sockets die before self.connected but running?
        self.screen_streamer.close()
        self.mouse_controller.close()
        try:
            # TODO: change kill to False
            self._app.connection_manager.close_connection("screen recorder", False)
            self._app.connection_manager.close_connection("mouse tracker", False)
        except Exception as e:
            logging.error(f"socket error while closing screen recorder: {e}")
