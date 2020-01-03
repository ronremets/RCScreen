"""
The controller screen.
"""

__author__ = "Ron Remets"

import io

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty, BooleanProperty, StringProperty
from kivy.uix.image import CoreImage
from kivy.clock import Clock

from Code.client import screen_recorder

app = App.get_running_app()


class ControllerScreen(Screen):
    """
    The screen where the client controls another client.
    """
    screen = ObjectProperty(None)
    is_controller = BooleanProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._screen_update_event = None
        self._screen_recorder = screen_recorder.ScreenRecorder()

    def _update_screen(self, *_):
        """
        Update the screen.
        """
        if app.is_controller:
            image_bytes = app.connection.recv()
            # It's None until other_client connects
            if image_bytes is not None:
                image_data = io.BytesIO(image_bytes)
                image_data.seek(0)
                self.screen.texture = CoreImage(image_data, ext="png").texture
                self.screen.reload()
        else:
            frame = self._screen_recorder.frame
            # It's None until other_client connects
            if frame is not None:
                app.connection.send({"content": frame})

    def on_enter(self, *args):
        """
        When this screen starts, start showing the screen.
        """
        if app.connection.is_controller:
            app.connection.start(self.code, self.other_code, False, True)
        else:
            app.connection.start(self.code, self.other_code, True, False)
        self._screen_recorder.start()
        self._screen_update_event = Clock.schedule_interval(
            self._update_screen, 0)

    def on_leave(self, *args):
        """
        When this screen stops, wait for screen to stop.
        """
        self._screen_update_event.cancel()
        app.connection.close(kill=True)  # TODO: change kill to False
        self._screen_recorder.close()
