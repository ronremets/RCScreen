"""
The controller screen.
"""

__author__ = "Ron Remets"

import threading
import io
import time
import logging

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty
from kivy.clock import Clock

from communication.advanced_socket import ConnectionClosed


class ControllerScreen(Screen):
    """
    The screen where the client controls another client.
    """
    controller = ObjectProperty()
    screen = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._app = App.get_running_app()

    def _start_mouse(self):
        """
        Start the thread that sends the mouse information.
        """
        self.controller.connection = self._app.connection_manager.connections[
            "mouse tracker"]
        self.controller.is_active = True

    def _handle_mouse_connection_status(self, connection_status):
        """
        Handle the connection status of the mouse connection.
        If it is fine than start the screen.
        :param connection_status: The connection status as a string.
        """
        logging.debug(
            f"MAIN:Mouse connection status: {connection_status}")
        # TODO: Handle errors
        Clock.schedule_once(lambda _: self._start_mouse())

    def _start_screen(self):
        """
        Start the screen streaming.
        """
        self.screen.connection = self._app.connection_manager.connections[
            "screen recorder"]
        self.screen.start()

    def _handle_screen_connection_status(self, connection_status):
        """
        Handle the connection status of the screen connection.
        If it is fine than start the screen.
        :param connection_status: The connection status as a string.
        """
        logging.debug(
            f"MAIN:Screen connection status: {connection_status}")
        # TODO: Handle errors
        Clock.schedule_once(lambda _: self._start_screen())

    def on_enter(self, *args):
        """
        When this screen starts, start showing the screen.
        """
        logging.info("MAIN:Creating mouse tracker connection")
        self._app.connection_manager.add_connection(
            self._app.username,
            "mouse tracker",
            (True, True),
            "mouse - sender",
            block=False,
            callback=self._handle_mouse_connection_status,
            only_send=True)
        logging.info("MAIN:Creating screen recorder connection")
        self._app.connection_manager.add_connection(
            self._app.username,
            "screen recorder",
            (False, True),
            "frame - receiver",
            block=False,
            callback=self._handle_screen_connection_status)

    def on_leave(self, *args):
        """
        Close all components.
        """
        # TODO: will crash if not finished before connection closes
        self.controller.is_alive = False
        self.screen.close()
        try:
            # TODO: change kill to False
            self._app.connection_manager.close_connection("screen recorder", False)
            self._app.connection_manager.close_connection("mouse tracker", False)
        except Exception as e:
            logging.error(f"socket error while closing screen recorder: {e}")
