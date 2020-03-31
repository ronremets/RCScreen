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
from kivy.uix.image import CoreImage
from kivy.clock import Clock

from communication.message import Message, MESSAGE_TYPES
from communication.advanced_socket import ConnectionClosed


class ControllerScreen(Screen):
    """
    The screen where the client controls another client.
    """
    screen = ObjectProperty()
    controller = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._app = App.get_running_app()
        self._mouse_info_update_thread = None
        self._frame_lock = threading.Lock()
        self._running_lock = threading.Lock()
        self._set_running(False)

    @property
    def running(self):
        """
        Check if the client is running.
        :return: True if it is, otherwise False
        """
        with self._running_lock:
            return self._running

    def _set_running(self, value):
        with self._running_lock:
            self._running = value

    def _start_mouse(self, connection_status):
        """
        Start the thread that sends the mouse information.
        :param connection_status: The connection status of the
                                  connection used to send the mouse
                                  information.
        """
        logging.debug(
            f"Received connection status for mouse: {connection_status}")
        self._mouse_info_update_thread = threading.Thread(
            name="Mouse info send thread",
            target=self._send_mouse_info)
        self._mouse_info_update_thread.start()

    def _send_mouse_info(self):
        """
        Send the mouse's information like position and buttons state
        """
        old_mouse_info = ""
        try:
            while self.running:
                new_mouse_info = repr(self.controller.mouse)
                if new_mouse_info != old_mouse_info:
                    logging.debug("MOUSE:mouse move")
                    self._app.connection_manager.connections["mouse tracker"].socket.send(Message(
                        MESSAGE_TYPES["controller"],
                        new_mouse_info))
                    # make sure the server is ready to receive to not fill
                    # its buffers
                    self._app.connection_manager.connections["mouse tracker"].socket.recv()
                    old_mouse_info = new_mouse_info
        except ConnectionClosed:
            logging.error("Unexpected socket close")

    def _start_screen(self, connection_status):
        """
        Start the screen streaming.
        The actual starting of the screen is done in the main thread
        so this method can be called from any thread.
        :param connection_status: The connection status of connecting
                                  the screen recorder
        """
        logging.debug(
            f"Received connection status for screen: {connection_status}")
        self.screen.connection = self._app.connection_manager.connections[
            "screen recorder"]
        Clock.schedule_once(lambda dt: self.screen.start())

    def on_enter(self, *args):
        """
        When this screen starts, start showing the screen.
        """
        logging.info("MAIN:Creating screen recorder connection")
        self._set_running(True)
        self._app.connection_manager.add_connection(
            self._app.username,
            "screen recorder",
            (False, True),
            "frame - receiver",
            block=False,
            callback=self._start_screen)
        logging.info("MAIN:Creating mouse tracker connection")
        self._app.connection_manager.add_connection(
            self._app.username,
            "mouse tracker",
            (True, True),
            "mouse - sender",
            block=False,
            callback=self._start_mouse)

    def on_leave(self, *args):
        """
        When this screen stops, wait for screen to stop.
        """
        self._set_running(False)
        self.screen.close()
        self._mouse_info_update_thread.join()
        try:
            # TODO: change kill to False
            self._app.connection_manager.close_connection("screen recorder", True)
            self._app.connection_manager.close_connection("mouse tracker", True)
        except Exception as e:
            logging.error(f"socket error while closing screen recorder: {e}")
