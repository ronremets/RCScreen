"""
The controlled screen.
"""

__author__ = "Ron Remets"

import threading
import time
import logging

import win32api
from kivy.app import App
from kivy.uix.screenmanager import Screen

from client.screen_recorder import ScreenRecorder
from communication.message import Message, MESSAGE_TYPES


class ControlledScreen(Screen):
    """
    The screen where the client is controlled by another client.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._screen_update_thread = None
        self._mouse_movement_update_thread = None
        self._mouse_click_update_thread = None
        self._screen_recorder = ScreenRecorder()
        self._running_lock = threading.Lock()
        self._app = App.get_running_app()
        self._set_running(False)

    @property
    def running(self):
        """
        Check if the client is running.
        :return: True if it is, otherwise False
        """
        with self._running_lock:
            return self.__running

    def _set_running(self, value):
        with self._running_lock:
            self.__running = value

    def _send_frame(self):
        """
        Send a frame of the screen
        """
        while self.running:
            frame = self._screen_recorder.frame
            # It's None until recording starts
            if frame is not None:
                self._app.connections["screen recorder"].send(Message(
                    MESSAGE_TYPES["controlled"],
                    frame))
            else:
                print("frame is None")

    def _mouse_movement_update(self):
        """
        Get the position og the mouse and move it to there
        """
        while self.running:
            # logging.debug("Updating mouse movement")
            point = self._app.connections["mouse movement tracker"].recv().get_content_as_text()
            x, y = point[1:-1].split(",")
            x, y = int(x), int(y)
            logging.debug(f"({x}, {y})")
            # win32api.SetCursorPos((x, y))

    def on_enter(self, *args):
        """
        When this screen starts, start showing the screen.
        """
        self._set_running(True)
        logging.info("Creating screen recorder connection")
        self._app.add_connection(
            "screen recorder",
            (True, False),
            "frame - sender")
        logging.info("Creating mouse movement tracker connection")
        self._app.add_connection(
            "mouse movement tracker",
            (False, True),
            "mouse movement - receiver")
        logging.info("Starting screen recorder")
        self._screen_recorder.start()
        logging.info("Starting updates")
        self._screen_update_thread = threading.Thread(
            target=self._send_frame)
        self._mouse_movement_update_thread = threading.Thread(
            target=self._mouse_movement_update)
        # self._mouse_click_update_thread = threading.Thread(
        #     target=None)
        self._screen_update_thread.start()
        self._mouse_movement_update_thread.start()
        # self._mouse_click_update_thread.start()
        logging.info("Started updates")

    def on_leave(self, *args):
        """
        When this screen stops, wait for screen to stop.
        """
        self._set_running(False)
        # TODO: blocking main thread here, add timeout or kill or something
        self._screen_update_thread.join()
        self._mouse_movement_update_thread.join()
        # self._mouse_click_update_thread.join()
        try:
            # TODO: change kill to False
            self._app.connections["screen recorder"].close(kill=True)
            self._app.connections["mouse movement tracker"].close(kill=True)
            # self._app.connections["mouse click tracker"].close(kill=True)
        except Exception as e:
            logging.error(f"socket error while closing screen recorder: {e}")
        finally:
            self._screen_recorder.close()
