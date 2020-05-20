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
from kivy.clock import Clock, mainthread

from communication.advanced_socket import ConnectionClosed
from communication.message import Message, MESSAGE_TYPES
from components.session_settings import SessionSettings
from ui.mouse import Mouse


class ControllerScreen(Screen):
    """
    The screen where the client controls another client.
    """
    mouse = ObjectProperty(Mouse())
    screen = ObjectProperty()
    keyboard_tracker = ObjectProperty()
    session_settings = ObjectProperty(SessionSettings())

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._app = App.get_running_app()

    def _update_screen_size_variable(self, *_):
        self._app.screen_size = self.screen.norm_image_size
        print("screen var updated to", self._app.screen_size)

    def _update_screen_size(self, *_):
        print(self.screen.size, self.screen.norm_image_size)
        width, height = self._app.screen_size
        print("var is", self._app.screen_size)
        if self.session_settings.running:
            self.session_settings.settings_updates.put(Message(
                MESSAGE_TYPES["controller"],
                f"other screen size:{width}, {height}"))

    def on_touch_down(self, touch):
        self.keyboard_tracker.show_keyboard()
        return super().on_touch_down(touch)

    @mainthread
    def _start_keyboard(self):
        self.keyboard_tracker.connection = self._app.connection_manager.client.get_connection(
            "keyboard tracker")
        self.keyboard_tracker.is_tracking = True

    def _handle_keyboard_connection_status(self, connection_status):
        logging.debug(
            f"MAIN:Keyboard connection status: {connection_status}")
        # TODO: Handle errors
        self._start_keyboard()

    @mainthread
    def _start_mouse(self):
        """
        Start the thread that sends the mouse information.
        """
        #self.controller.connection = self._app.connection_manager.connections[
        #    "mouse tracker"]
        #self.controller.is_active = True
        self.mouse.connection = self._app.connection_manager.client.get_connection(
            "mouse tracker")
        self.mouse.is_tracking = True

    def _handle_mouse_connection_status(self, connection_status):
        """
        Handle the connection status of the mouse connection.
        If it is fine than start the screen.
        :param connection_status: The connection status as a string.
        """
        logging.debug(
            f"MAIN:Mouse connection status: {connection_status}")
        # TODO: Handle errors
        self._start_mouse()

    @mainthread
    def _start_settings(self):
        self.session_settings.start(
            self._app.connection_manager.client.get_connection("settings"))
        self._update_screen_size_variable()

    def _handle_settings_connection_status(self, connection_status):
        logging.debug(
            f"MAIN:Settings connection status: {connection_status}")
        # TODO: Handle errors
        self._start_settings()

    @mainthread
    def _start_screen(self):
        """
        Start the screen streaming.
        """
        self.screen.connection = self._app.connection_manager.client.get_connection(
            "screen recorder")
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
        self._start_screen()

    def on_enter(self, *args):
        """
        Start the screen
        """
        # TODO: what if texture changes? screen size does not update!
        #  for example, if the size of the raw image of the screen changes
        self.screen.bind(size=self._update_screen_size_variable)
        self._app.bind(screen_size=self._update_screen_size)

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
        self._app.connection_manager.add_connection(
            self._app.username,
            "keyboard tracker",
            (True, True),
            "keyboard - sender",
            block=False,
            callback=self._handle_keyboard_connection_status)
        self._app.connection_manager.add_connection(
            self._app.username,
            "settings",
            (True, True),
            "settings",
            block=False,
            callback=self._handle_settings_connection_status)

    def on_leave(self, *args):
        """
        Close all components.
        """
        # TODO: will crash if not finished before connection closes
        #self.controller.is_alive = False
        self.mouse.is_tracking = False
        self.screen.stop()
        self.keyboard_tracker.is_tracking = False
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
