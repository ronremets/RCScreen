"""
The controller screen.
"""

__author__ = "Ron Remets"

from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty
import threading
import time
import PIL


class ControllerScreen(Screen):
    """
    The screen where the client controls another client.
    """
    screen_thread = threading.Thread(target=ControllerScreen._update_screen)
    screen = ObjectProperty(None)

    @staticmethod
    def _update_screen():
        for i in range(4):
            # ControllerScreen.screen.source = PIL.grab()
            ControllerScreen.screen.reload()
            time.sleep(1)

    def on_enter(self, *args):
        """
        When this screen starts, start showing the screen.
        """
        ControllerScreen.screen_thread.start()

    def on_leave(self, *args):
        """
        When this screen stops, wait for screen to stop.
        """
        ControllerScreen.screen_thread.join()
