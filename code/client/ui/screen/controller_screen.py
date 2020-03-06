"""
The controller screen.
"""

__author__ = "Ron Remets"

import threading
import io
import time

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty, BooleanProperty, StringProperty
from kivy.uix.image import CoreImage
from kivy.clock import Clock

from client import screen_recorder
from communication.message import Message, MESSAGE_TYPES

ctr = 0
class ControllerScreen(Screen):
    """
    The screen where the client controls another client.
    """
    screen = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._screen_update_event = None
        self._screen_recorder = screen_recorder.ScreenRecorder()
        self._running_lock = threading.Lock()
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
        app = App.get_running_app()
        while self.running:
            frame = self._screen_recorder.frame
            # It's None until other_client connects
            if frame is not None:
                app.connections["screen recorder"].send(Message(
                    MESSAGE_TYPES["controlled"],
                    frame))  # TODO: also do this in another thread
            time.sleep(0.1)  # TODO: remove?

    def _update_screen(self, *_):
        """
        Update the screen.
        """
        global ctr
        ctr += 1
        print(ctr,end="| ")
        app = App.get_running_app()
        image_bytes = app.connections["screen recorder"].recv().content  # TODO: do this in another thread
        print(f"{{{len(image_bytes)}}}")
        # It's None until other_client connects
        if image_bytes is not None:
            image_data = io.BytesIO(image_bytes)
            image_data.seek(0)
            # print("len of none is " + str(len(image_data)))
            print(image_data)
            self.screen.texture = CoreImage(image_data, ext="png").texture
            self.screen.reload()

    def on_enter(self, *args):
        """
        When this screen starts, start showing the screen.
        """
        app = App.get_running_app()
        # app.add_connection("screen recorder", (True, False), "frame")
        print("creating connection")
        self._set_running(True)
        if app.is_controller:  # TODO: think of a better name maybe put in dict
            app.add_connection("screen recorder", (True, False), "frame - sender")
            print("starting screen recorder")
            self._screen_recorder.start()
            print("starting updates")
            self._screen_update_event = threading.Thread(
                target=self._send_frame)
            self._screen_update_event.start()
        else:
            app.add_connection("screen recorder", (False, True), "frame - receiver")
            print("starting updates")
            self._screen_update_event = Clock.schedule_interval(
                self._update_screen, 0)

    def on_leave(self, *args):
        """
        When this screen stops, wait for screen to stop.
        """
        app = App.get_running_app()
        self._set_running(False)
        if app.is_controller:
            self._screen_update_event.cancel()
        else:
            self._screen_update_event.join()  # TODO: blocking main thread here, add timeout or kill or something
        try:
            app.connection.close(kill=True)  # TODO: change kill to False
        except Exception as e:
            print("socket error while closing: " + str(e))
        self._screen_recorder.close()
