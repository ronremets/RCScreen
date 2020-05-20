"""
The controlled screen.
"""

__author__ = "Ron Remets"

import threading
import time
import logging
import win32api

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty
from kivy.core.window import Window

from components.mouse_controller import MouseController
from components.screen_streamer import ScreenStreamer
from components.keyboard_controller import KeyboardController
from components.session_settings import SessionSettings
from communication.message import Message, MESSAGE_TYPES


class ControlledScreen(Screen):
    """
    The screen where the client is controlled by another client.
    """
    mouse_controller = ObjectProperty(MouseController())
    screen_streamer = ObjectProperty(ScreenStreamer())
    keyboard_controller = ObjectProperty(KeyboardController())
    session_settings = ObjectProperty(SessionSettings())

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._app = App.get_running_app()

    def update_screen_size(self, size):
        width, height = size
        self._app.screen_size = size
        if self.session_settings.running:
            self.session_settings.settings_updates.put(Message(
                MESSAGE_TYPES["controlled"],
                f"other screen size:{width}, {height}"))

    def _start_mouse_controller(self, connection_status):
        """
        Start the mouse_controller.
        :param connection_status: The connection status of the
                                  connection used to by the mouse
        """
        self.mouse_controller.start(
            self._app.connection_manager.client.get_connection("mouse tracker"))

    def _start_screen_streamer(self, connection_status):
        """
        Start the screen streamer.
        :param connection_status: The connection status of the
                                  connection used to stream
        """
        #self.screen_streamer.screen_recorder.image_format = self._app.screen_image_format
        self.screen_streamer.start(
            self._app.connection_manager.client.get_connection("screen recorder"))

    def _start_keyboard(self, connection_status):
        self.keyboard_controller.start(
            self._app.connection_manager.client.get_connection("keyboard tracker"))

    def _handle_settings_connection_status(self, connection_status):
        logging.debug(
            f"MAIN:Settings connection status: {connection_status}")
        # TODO: Handle errors
        Clock.schedule_once(lambda _: self._start_settings())

    def _start_settings(self):
        self.session_settings.start(
            self._app.connection_manager.client.get_connection("settings"))
        self.update_screen_size((win32api.GetSystemMetrics(0),
                                 win32api.GetSystemMetrics(1)))

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
        logging.info("Creating keyboard tracker connection")
        self._app.connection_manager.add_connection(
            self._app.username,
            "keyboard tracker",
            (True, True),
            "keyboard - receiver",
            block=False,
            callback=self._start_keyboard)
        self._app.connection_manager.add_connection(
            self._app.username,
            "settings",
            (True, True),
            "settings",
            block=False,
            callback=self._handle_settings_connection_status)

    def on_leave(self, *args):
        """
        When this screen stops, wait for screen to stop.
        """
        # TODO: what happens if sockets die before self.connected but running?
        self.screen_streamer.close()
        self.mouse_controller.close()
        self.keyboard_controller.close()
        self.session_settings.close()
        for connection_name in ("screen recorder",
                                "mouse tracker",
                                "keyboard tracker",
                                "settings"):
            try:
                # TODO: change kill to False
                self._app.connection_manager.close_connection(connection_name)
            except Exception:
                logging.error(f"CONTROLLED SCREEN:Error while closing"
                              f" {connection_name}", exc_info=True)
