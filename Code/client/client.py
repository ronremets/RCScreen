"""
This is the entry point of the client's application.
"""

__author__ = "Ron Remets"

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import AliasProperty

# noinspection PyUnresolvedReferences
import ui


class RCScreenApp(App):
    """
    Responsible for the whole client's application.
    """

    def build(self):
        """
        Builds the application.
        :return: The application object.
        """
        return Builder.load_file("RCScreen.kv")


if __name__ == '__main__':
    RCScreenApp().run()
