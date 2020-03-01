"""
The signup screen.
"""

__author__ = "Ron Remets"

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty

from client.main import SERVER_ADDRESS
from communication.advanced_socket import AdvancedSocket
from communication.message import Message, MESSAGE_TYPES
from communication import communication_protocol
# from data import user


class SignupScreen(Screen):
    """
    The screen where the client signs up to the server
    """
    signup_button = ObjectProperty(None)
    username_text_input = ObjectProperty(None)
    password_text_input = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_signup_button_press(self, _):
        """
        Signup to the server.
        :param _: The touch object (not used)
        """
        print("signing in")
        app = App.get_running_app()
        app.username = self.username_text_input.text
        app.password = self.password_text_input.text
        app.add_connection("main", (True, True), "main", method="signup")
        print("signed up")
        # if logged_in:
        self.manager.transition.direction = "up"
        app.root.current = "main"
