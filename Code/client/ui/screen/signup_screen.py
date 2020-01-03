"""
The signup screen.
"""

__author__ = "Ron Remets"

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty

from data import user


class SignupScreen(Screen):
    """
    The screen where the client signs up to the server
    """
    login_button = ObjectProperty(None)
    username_text_input = ObjectProperty(None)
    password_text_input = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_signup_button_press(self, _):
        """
        Signup to the server.
        :param _: The touch object (not used)
        """
        app = App.get_running_app()
        app.user = user.User(
            self.username_text_input.text,
            self.password_text_input.text)
        print(app.user)
        return True
