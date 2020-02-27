"""
This is the entry point of the client's application.
"""

__author__ = "Ron Remets"

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty


# noinspection PyUnresolvedReferences
import ui

SERVER_ADDRESS = ("127.0.0.1", 2125)


class RCScreenApp(App):
    """
    Responsible for the whole client's application.
    """
    username = StringProperty()
    password = StringProperty()
    connections = ObjectProperty(dict())

    def add_connection(self, address, name, buffer_state):
        """
        Add a connection to app. Only call this after sign in or log in.
        :param address: The address to connect to
        :param name: The name of the connection
        :param buffer_state: a tuple like
               (input is buffered, output is buffered)
        """
        # TODO: add a way to add connections
        # TODO: connect with token you get in log in

    def build(self):
        """
        Builds the application.
        :return: The application object.
        """
        return Builder.load_file("RCScreen.kv")


if __name__ == '__main__':
    RCScreenApp().run()
