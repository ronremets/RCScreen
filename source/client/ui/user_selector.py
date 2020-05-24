"""
Show and select connected users
"""
__author__ = "Ron Remets"

from kivy.app import App
from kivy.clock import Clock
from kivy.properties import (ObjectProperty,
                             BooleanProperty,
                             ListProperty,
                             StringProperty)
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivy.logger import Logger

from communication.message import Message, MESSAGE_TYPES
from communication.advanced_socket import ConnectionClosed

UPDATE_USERS_REFRESH_RATE = 1.5


class UserSelector(Button):
    """
    Show and select connected users
    """
    is_active = BooleanProperty(False)
    users_dropdown = ObjectProperty(None)
    usernames = ListProperty()
    selected_username = StringProperty()
    _connection = ObjectProperty(None)
    _update_event = ObjectProperty(None)
    _updating_users = BooleanProperty(False)
    _new_user_selected = BooleanProperty(False)
    _selecting_user = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._app = App.get_running_app()
        self.users_dropdown = DropDown(on_select=self._select_user)
        print("constructor called")

    def _select_user(self, _, username):
        """
        Select a user
        :param username: The username to select
        """
        self.selected_username = username
        self._new_user_selected = True
        Logger.info(f"User selector:Selected partner: {username}")

    def _check_for_usernames_response(self):
        return self._connection.socket.recv(block=False)

    @staticmethod
    def _handle_usernames_response(response):
        """
        parse the usernames from the server response
        :param response: The response the server sent
        :return: A list of the usernames the server sent
        """
        usernames = response.get_content_as_text().split(", ")
        Logger.debug(
            f"User selector:Received usernames: {usernames}")
        return usernames

    def _update_dropdown(self, usernames):
        """
        Update the list of the usernames the dropdown displays
        :param usernames: The usernames to display
        """
        self.users_dropdown.clear_widgets()
        for username in usernames:
            self.users_dropdown.add_widget(Button(
                size_hint_y=None,
                size=self.size,
                text=username,
                on_release=lambda button:
                self.users_dropdown.select(button.text)))

    def _check_for_select_response(self):
        return self._connection.socket.recv(block=False)

    def _handle_select_response(self, response):
        pass

    def _finnish_selecting(self):
        self._app.partner = self.selected_username

    def _send_usernames_request(self):
        Logger.debug("User selector:Requesting usernames")
        self._connection.socket.send(Message(
            MESSAGE_TYPES["server interaction"],
            "get all connected usernames"))

    def _send_select_request(self):
        Logger.debug(
            f"User selector:Sending set partner: {self.selected_username}")
        self._connection.socket.send(Message(
            MESSAGE_TYPES["server interaction"],
            f"set partner\n{self.selected_username}"))

    def _update_users(self, _):
        try:
            if self._updating_users:
                usernames_response = self._check_for_usernames_response()
                if usernames_response is not None:
                    usernames = UserSelector._handle_usernames_response(
                        usernames_response)
                    self._update_dropdown(usernames)
                    self._updating_users = False
            elif self._selecting_user:
                select_response = self._check_for_select_response()
                if select_response is not None:
                    self._handle_select_response(select_response)
                    self._finnish_selecting()
                    self._selecting_user = False
            elif self._new_user_selected:
                self._send_select_request()
                self._selecting_user = True
                self._new_user_selected = False
            else:
                self._send_usernames_request()
                self._updating_users = True
        except ConnectionClosed:  # Unexpected close
            Logger.error("User selector:Unexpected close, closing!")
            self.close()
        except Exception as e:  # TODO: be more specific
            print(e)
            Logger.error("User selector:Unexpected error, closing!",
                         exc_info=True)
            self.close()

    def on_release(self):
        """
        Open the dropdown
        """
        Logger.debug("User selector:Attempting to open dropdown")
        if self.is_active:
            Logger.debug("User selector:Opening dropdown")
            self.users_dropdown.open(self)
        else:
            Logger.debug("User selector:Did not open dropdown "
                         "since it is closed or had not started")

    def start(self, connection):
        """
        Start receiving users and displaying them
        :param connection: The connection to get the users with
        """
        Logger.info("User selector:Starting")
        self.is_active = True
        self._connection = connection
        self._update_event = Clock.schedule_interval(
            self._update_users, UPDATE_USERS_REFRESH_RATE)

    def close(self):
        """
        Close the users getter
        Only call this after opening
        """
        Logger.info("User selector:Closing")
        self.is_active = False
        if self._update_event is not None:
            self._update_event.cancel()
