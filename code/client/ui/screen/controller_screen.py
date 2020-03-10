"""
The controller screen.
"""

__author__ = "Ron Remets"

import threading
import io
import time
import logging
import win32api

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty, BooleanProperty, StringProperty
from kivy.uix.image import CoreImage
from kivy.clock import Clock

from client.mouse_movement_tracker import MouseMovementTracker
from client.mouse_click_tracker import MouseClickTracker
from communication.message import Message, MESSAGE_TYPES
from communication.communication_protocol import ENCODING


class ControllerScreen(Screen):
    """
    The screen where the client controls another client.
    """
    screen = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._app = App.get_running_app()
        self._frame = None
        self._receive_frames_thread = None
        self._screen_update_event = None
        self._frame_receiver_thread = None
        self._mouse_movement_update_thread = None
        self._frame_lock = threading.Lock()
        self._mouse_movement_tracker = MouseMovementTracker()
        # self._mouse_click_tracker = MouseClickTracker()
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

    def _receive_frame(self):
        """
        receive a frame and update self._frame
        """
        while self.running:
            frame = self._app.connections["screen recorder"].recv().content
            with self._frame_lock:
                self._frame = frame

    def _update_screen(self, *_):
        """
        Update the screen.
        """
        logging.debug("Updating controller screen")
        # TODO: do this in another thread in another object maybe?
        with self._frame_lock:
            image_bytes = self._frame
        # It's None until other_client connects
        if image_bytes is not None:
            logging.debug(f"Length of frame bytes: {len(image_bytes)}")
            image_data = io.BytesIO(image_bytes)
            image_data.seek(0)
            self.screen.texture = CoreImage(image_data, ext="png").texture
            self.screen.reload()
        else:
            logging.warning("OTHER USER NOT CONNECTED")

    def _send_mouse_position(self):
        """
        Send the mouse position
        """
        while self.running:
            position = self._mouse_movement_tracker.current_position
            # It's None until tracking starts
            if position is not None:
                self._app.connections["mouse movement tracker"].send(Message(
                    MESSAGE_TYPES["controller"],
                    str(position).encode(ENCODING)))
            time.sleep(5)  # TODO: remove?

    def _send_mouse_buttons_state(self):
        """
        Sends the state of the buttons of the mouse
        """
        while self.running:
            buttons_state = self._mouse_click_tracker.buttons_state
            # It's None until tracking starts
            if buttons_state is not None:
                self._app.connections["mouse movement tracker"].send(Message(
                    MESSAGE_TYPES["controlled"],
                    buttons_state))
            time.sleep(1)  # TODO: remove?

    def on_enter(self, *args):
        """
        When this screen starts, start showing the screen.
        """
        logging.info("Creating screen recorder connection")
        self._set_running(True)
        self._app.add_connection(
            "screen recorder",
            (False, True),
            "frame - receiver")
        logging.info("Creating mouse movement tracker connection")
        self._app.add_connection(
            "mouse movement tracker",
            (True, False),
            "mouse movement - sender")
        # logging.info("Creating mouse click tracker connection")
        # self._app.add_connection(
        #     "mouse click tracker",
        #     (True, False),
        #     "mouse click - sender")
        logging.info("Starting mouse movement tracker")
        self._mouse_movement_tracker.start()
        # logging.info("Starting mouse click tracker")
        # self._mouse_click_tracker.start()
        logging.info("Starting updates")
        self._receive_frames_thread = threading.Thread(
            target=self._receive_frame)
        self._screen_update_event = Clock.schedule_interval(
            self._update_screen, 0)
        self._mouse_movement_update_thread = threading.Thread(
            target=self._send_mouse_position)
        # self._mouse_movement_update_thread = threading.Thread(
        #     target=self._send_mouse_buttons_state)
        self._receive_frames_thread.start()
        self._mouse_movement_update_thread.start()
        # self._mouse_click_update_thread.start()
        logging.info("Started updates")

    def on_leave(self, *args):
        """
        When this screen stops, wait for screen to stop.
        """
        app = App.get_running_app()
        self._set_running(False)
        self._screen_update_event.cancel()
        self._receive_frames_thread.join()
        self._mouse_movement_update_thread.join()
        # self._mouse_click_update_thread.join()
        try:
            # TODO: change kill to False
            app.connections["screen recorder"].close(kill=True)
            app.connections["mouse movement tracker"].close(kill=True)
            # self._app.connections["mouse click tracker"].close(kill=True)
        except Exception as e:
            logging.error(f"socket error while closing screen recorder: {e}")
        finally:
            self._mouse_movement_tracker.close()
            # self._mouse_click_tracker.close()
