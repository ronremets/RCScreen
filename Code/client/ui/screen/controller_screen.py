"""
The controller screen.
"""

__author__ = "Ron Remets"

import io
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty, BooleanProperty, StringProperty
from kivy.uix.image import CoreImage
from kivy.clock import Clock

import advanced_socket
import screen_recorder


class ControllerScreen(Screen):
    """
    The screen where the client controls another client.
    """
    screen = ObjectProperty()
    is_controller = BooleanProperty()
    code = StringProperty()
    other_code = StringProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._screen_update_event = None
        self._socket = advanced_socket.AdvancedSocket()
        self._screen_recorder = screen_recorder.ScreenRecorder()

    def _update_screen(self, *_):
        """
        Update the screen.
        """
        if self.is_controller:
            image_bytes = self._socket.data_received
            # It's None until other_client connects
            if image_bytes is not None:
                image_data = io.BytesIO(image_bytes)
                image_data.seek(0)
                #image = PIL.Image.frombytes(
                #    'RGB',
                #    len(image_bytes),
                #    image_bytes,
                #    'raw',
                #    'BGRX')
                self.screen.texture = CoreImage(image_data, ext="png").texture
                self.screen.reload()
        else:
            frame = self._screen_recorder.frame
            # It's None until other_client connects
            if frame is not None:
                self._socket.data_to_send = {"content": frame}

    def on_enter(self, *args):
        """
        When this screen starts, start showing the screen.
        """
        print("other_code:", self.other_code)
        self._socket.start(self.code, self.other_code)
        self._screen_recorder.start()
        self._screen_update_event = Clock.schedule_interval(
            self._update_screen, 0)

    def on_leave(self, *args):
        """
        When this screen stops, wait for screen to stop.
        """
        self._screen_update_event.cancel()
        self._socket.close(kill=True)  # TODO: change kill to False
        self._screen_recorder.close()
