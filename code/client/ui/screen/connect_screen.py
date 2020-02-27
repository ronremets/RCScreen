"""
The connect screen.
"""

__author__ = "Ron Remets"

import threading

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivy.clock import Clock

from communication.message import Message, MESSAGE_TYPES
from communication import communication_protocol


class ConnectScreen(Screen):
    """
    The screen where the client connects to another client
    """
    partner_label = ObjectProperty(None)
    users_grid = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._connected_users_lock = threading.Lock()
        self._all_users_lock = threading.Lock()
        self._connected_users = []
        self._all_users = []
        Clock.schedule_event(self.refresh_users, 5)
        # TODO: add one socket for users update and for one for
        #  set partner and connect
        # TODO: just use more sockets

    def update_users(self):
        """
        Get the users from the server and update the lists
        """
        app = App.get_running_app()
        app.connections["main"].send(Message(
            MESSAGE_TYPES["server interaction"],
            "get all connected usernames".encode(
                communication_protocol.ENCODING)))
        usernames = app.connections["main"].recv().get_content_as_text()
        usernames = usernames[1:-1].split(", ")
        with self._connected_users_lock:
            self._connected_users = usernames

        app.connections["main"].send(Message(
            MESSAGE_TYPES["server interaction"],
            "get all usernames".encode(
                communication_protocol.ENCODING)))
        usernames = app.connections["main"].recv().get_content_as_text()
        usernames = usernames[1:-1].split(", ")
        with self._all_users_lock:
            self._all_users = usernames

    def refresh_users(self, _):
        """
        Start the threads that refresh the usernames lists
        :param _: The time between calls
        :return: False on error, otherwise True
        """
        threading.Thread(target=self.update_users).start()
        return True

    def format_usernames(self): # TODO: delete this
        """
        format all the usernames
        :return: a string with all the usernames
        """
        active = self.get_active_usernames()[1:-1].split(", ")
        all_users = self.get_all_usernames()[1:-1].split(", ")
        return (str(active)
                + "|"
                + str([*filter(lambda x: x not in active, all_users)]))

    def select_username(self, button):
        print("I am selecting")
        self.partner_label.text = f"Partner: {button.text}"
        print(self.partner_label.text)

    def create_grid(self):
        """
        Create the drop down that shows users
        """
        print("much before child:" + str(self.users_grid.children))
        connected_users = self.get_active_usernames()[1:-1].split(", ")
        print(f"connected users: {connected_users}")
        all_users = self.get_all_usernames()[1:-1].split(", ")
        disconnected_users = filter(
            lambda username: username not in connected_users, all_users)
        #self.enable = False
        #self.enable = True
        self.users_grid.clear_widgets()
        print("before child:" + str(self.users_grid.children))
        for username in connected_users:
            self.users_grid.rows += 1
            print(f"username: {username}")
            self.users_grid.add_widget(Button(
                text=username,
                size_hint_y=None,
                height=20,
                on_press=self.select_username))
        # TODO: there is a reference problem here where we have
        #  the button change through the different usernames.
        #  go search lambda funcs in for loops problems
        for username in disconnected_users:
            self.users_grid.rows += 1
            print(f"other username: {username}")
            self.users_grid.add_widget(Button(
                text=username,
                size_hint_y=None,
                height=40,
                on_press=self.select_username))
        print("after child:" + str(self.users_grid.children))
