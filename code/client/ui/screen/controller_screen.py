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
        self._frame = None
        self._receive_frames_thread = None
        self._screen_update_event = None
        self._frame_receiver_thread = None
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

    def _receive_frame(self):
        """
        receive a frame and update self._frame
        """
        while "screen recorder" not in self._app.connections.keys():
            pass
        while not self._app.connection_manager.connections["screen recorder"].connected:
            pass
        logging.info("Screen connected")
        while self.running:
            frame = self._app.connection_manager.connections["screen recorder"].recv().content
            with self._frame_lock:
                self._frame = frame

    def _update_screen(self, *_):
        """
        Update the screen.
        """
        # logging.debug("Updating controller screen")
        with self._frame_lock:
            image_bytes = self._frame
            self._frame = None  # Do not reload the same image
        # It's None until other_client connects
        if image_bytes is not None:
            a = time.time()
            logging.debug(f"Length of frame bytes: {len(image_bytes)}")
            image_data = io.BytesIO(image_bytes)
            image_data.seek(0)
            # TODO: create coreimage in receive frame thread and it should improve ~0.15 sec
            #  after testing it seems that only the sockets are readly the problem
            #  capturting and preparing to send as well as reloading does not tke time
            #  HOWEVER THIS METHOD IS IN KIVY'S THREAD AND BLOCKS IT !!!YOU MUST OPTIMIZE
            #  THIS AS MUCH AS YOU CAN!!!!
            self.screen.texture = CoreImage(image_data, ext="png").texture
            self.screen.reload()
            print(time.time() - a)
        #else:
        #    logging.warning("OTHER USER NOT CONNECTED OR DUP IMAGE")

    def _send_mouse_info(self):
        """
        Send the mouse's information like position and buttons state
        """
        while "mouse tracker" not in self._app.connections.keys():
            pass
        while not self._app.connection_manager.connections["mouse tracker"].connected:
            pass
        old_mouse_info = ""
        while self.running:
            new_mouse_info = repr(self.controller.mouse)
            if new_mouse_info != old_mouse_info:
                self._app.connection_manager.connections["mouse tracker"].send(Message(
                    MESSAGE_TYPES["controller"],
                    new_mouse_info))
                old_mouse_info = new_mouse_info

    def on_enter(self, *args):
        """
        When this screen starts, start showing the screen.
        """
        logging.info("Creating screen recorder connection")
        self._set_running(True)
        self._app.connection_manager.add_connection(
            "screen recorder",
            (False, True),
            "frame - receiver")
        logging.info("Creating mouse tracker connection")
        self._app.connection_manager.add_connection(
            "mouse tracker",
            (True, False),
            "mouse - sender")
        logging.info("Starting updates")
        self._receive_frames_thread = threading.Thread(
            target=self._receive_frame)
        self._screen_update_event = Clock.schedule_interval(
            self._update_screen, 0)
        self._mouse_info_update_thread = threading.Thread(
            target=self._send_mouse_info)
        self._receive_frames_thread.start()
        self._mouse_info_update_thread.start()
        logging.info("Started updates")

    def on_leave(self, *args):
        """
        When this screen stops, wait for screen to stop.
        """
        self._set_running(False)
        self._screen_update_event.cancel()
        self._receive_frames_thread.join()
        self._mouse_movement_update_thread.join()
        try:
            # TODO: change kill to False
            self._app.connection_manager.close_connection("screen recorder", True)
            self._app.connection_manager.close_connection("mouse movement tracker", True)
        except Exception as e:
            logging.error(f"socket error while closing screen recorder: {e}")
        finally:
            pass
