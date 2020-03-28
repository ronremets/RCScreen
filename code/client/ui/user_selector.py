"""
Show and select connected users
"""
__author__ = "Ron Remets"

from kivy.app import App
from kivy.clock import Clock
from kivy.properties import NumericProperty, ObjectProperty
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown

from user_getter import UserGetter

DEFAULT_BATCH_HEIGHT = 3
UPDATE_USERS_REFRESH_RATE = 3


def _select_user(instance, username):
    """
    Select a user
    :param instance: The instance who called select
    :param username: The username to select
    """
    app = App.get_running_app()
    app.partner = username
    print(f"Selected partner: {app.partner}")


class UserSelector(Button):
    """
    Show and select connected users
    """
    users_dropdown = ObjectProperty(DropDown(on_select=_select_user))
    _user_getter = ObjectProperty(UserGetter())
    _connection = ObjectProperty(None)
    _update_users_event = ObjectProperty(None)

    def _update_users(self, _):
        usernames = self._user_getter.users
        print(f"usernames: {usernames}")
        self.users_dropdown.clear_widgets()
        for username in usernames:
            self.users_dropdown.add_widget(Button(
                size_hint_y=None,
                size=self.size,
                text=username,
                on_release=lambda button:
                    self.users_dropdown.select(button.text)))

    def on_release(self):
        """
        Open the dropdown
        """
        self.users_dropdown.open(self)

    def start(self, connection):
        """
        Start receiving users and displaying them
        :param connection: The connection to get the users with
        """
        self._user_getter.start(connection)
        self._update_users_event = Clock.schedule_interval(
            self._update_users, UPDATE_USERS_REFRESH_RATE)

    def close(self, timeout=None):
        """
        Close the users getter
        Only call this after opening
        :param timeout: If not None, the time to wait before crashing
        """
        self._update_users_event.cancel()
        self._user_getter.close(timeout=timeout)
        self.users_dropdown.dismiss()
