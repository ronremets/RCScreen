"""
The login screen.
"""

__author__ = "Ron Remets"

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty

from client.main import SERVER_ADDRESS
from communication.advanced_socket import AdvancedSocket
from communication.message import Message, MESSAGE_TYPES
from communication import communication_protocol


class LoginScreen(Screen):
    """
    The screen where the client logs to the server
    """
    login_button = ObjectProperty(None)
    username_text_input = ObjectProperty(None)
    password_text_input = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_login_button_press(self, _):
        """
        login to the server.
        :param _: The touch object (not used)
        """
        print("logging in")
        app = App.get_running_app()
        app.username = self.username_text_input.text
        app.password = self.password_text_input.text
        app.connection = AdvancedSocket(SERVER_ADDRESS)
        app.connection.start(True, True)
        app.connection.send(Message(
            MESSAGE_TYPES["server interaction"],
            "login".encode(communication_protocol.ENCODING)))
        app.connection.send(Message(
            MESSAGE_TYPES["server interaction"],
            (app.username + "\n" + app.password + "\nmain").encode(
                communication_protocol.ENCODING)))
        print("finished logging in")
        return True
