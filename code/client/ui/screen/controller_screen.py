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
from communication.communication_protocol import ENCODING


class ControllerScreen(Screen):
    """
    The screen where the client controls another client.
    """
    screen = ObjectProperty()
    controller = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._app = App.get_running_app()
        #self._frame = None
        #self._receive_frames_thread = None
        #self._screen_update_event = None
        #self._frame_receiver_thread = None
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

    def _send_mouse_info(self):
        """
        Send the mouse's information like position and buttons state
        """
        while self._app.connection_manager.connections["mouse tracker"] is None:
            if not self.running or not self._app.connection_manager.running:
                raise NotImplementedError()  # TODO: what happens when closed?
        while not self._app.connection_manager.connections["mouse tracker"].connected:
            if not self.running or not self._app.connection_manager.running:
                raise NotImplementedError()  # TODO: what happens when closed?
        old_mouse_info = ""
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

    def on_enter(self, *args):
        """
        When this screen starts, start showing the screen.
        """
        logging.info("Creating screen recorder connection")
        self._set_running(True)
        self._app.connection_manager.add_connection( # TODO: let streamed_image do this
            self._app.username,
            "screen recorder",
            (False, True),  # TODO: look at this
            "frame - receiver",
            block=True)  # TODO: remove this
        logging.info("Creating mouse tracker connection")
        self._app.connection_manager.add_connection(
            self._app.username,
            "mouse tracker",
            (True, False),  # TODO: look at this
            "mouse - sender",
            block=True)
        logging.info("Starting updates")
        #self._receive_frames_thread = threading.Thread(
        #    target=self._receive_frame)
        #self._screen_update_event = Clock.schedule_interval(
        #    self._update_screen, 0)
        self._mouse_info_update_thread = threading.Thread(
            target=self._send_mouse_info)
        self.screen.start(self._app.connection_manager.connections["screen recorder"].socket,
                          "png")
        #self._receive_frames_thread.start()
        self._mouse_info_update_thread.start()
        logging.info("Started updates")

    def on_leave(self, *args):
        """
        When this screen stops, wait for screen to stop.
        """
        self._set_running(False)
        self.screen.close()
        #self._screen_update_event.cancel()
        #self._receive_frames_thread.join()
        self._mouse_movement_update_thread.join()
        try:
            # TODO: change kill to False
            self._app.connection_manager.close_connection("screen recorder", True)
            self._app.connection_manager.close_connection("mouse movement tracker", True)
        except Exception as e:
            logging.error(f"socket error while closing screen recorder: {e}")
