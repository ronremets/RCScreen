"""
The connect screen.
"""

__author__ = "Ron Remets"

import logging
import threading
import time

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
    controller_checkbox = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._app = App.get_running_app()
        self._connected_users_lock = threading.Lock()
        self._all_users_lock = threading.Lock()
        self._get_users_lock = threading.Lock()
        with self._get_users_lock:
            self._get_users = True
        self._connected_users = None
        self._all_users = None
        self._get_users_thread = None
        # TODO: add one socket for users update and for one for
        #  set partner and connect
        # TODO: just use more sockets

    def connect_to_partner(self):
        # TODO: run this on another thread and check progress in main
        #  thread
        # TODO: is main connected? check here or assume it is connected?
        self._app.connection_manager.connections["main"].send(Message(
            MESSAGE_TYPES["server interaction"],
            f"set partner\n{self._app.partner}"))
        response = self._app.connection_manager.connections["main"].recv()
        response = response.get_content_as_text()
        logging.debug(f"MAIN:answer to partner: {response}")

    def get_users(self):
        """
        Get the users from the server and update the lists
        """
        while "get users" not in self._app.connection_manager.connections.keys():
            pass
        # TODO: why is this needed? didnt you fix this?
        while not self._app.connection_manager.connections["get users"] is not None:
            pass
        while not self._app.connection_manager.connections["get users"].connected:
            pass
        while True:
            with self._get_users_lock:
                run = self._get_users
            if not run:
                logging.info("Closing get users thread")
                break
            time.sleep(1)
            logging.debug("sending get connected users request")
            self._app.connection_manager.connections["get users"].send(Message(
                MESSAGE_TYPES["server interaction"],
                "get all connected usernames"))
            usernames = self._app.connection_manager.connections["get users"].recv().get_content_as_text()
            usernames = usernames.split(", ")

            with self._connected_users_lock:
                self._connected_users = usernames

            logging.debug("sending get all users request")
            self._app.connection_manager.connections["get users"].send(Message(
                MESSAGE_TYPES["server interaction"],
                "get all usernames"))
            usernames = self._app.connection_manager.connections["get users"].recv().get_content_as_text()
            usernames = usernames.split(", ")
            with self._all_users_lock:
                self._all_users = usernames

    def select_username(self, button):
        logging.info(f"selected partner to be {button.text}")
        # TODO: pick partner here?
        self._app.partner = button.text
        self.partner_label.text = f"Partner: {button.text}"

    def create_grid(self):
        """
        Create the drop down that shows users
        """
        """print("much before child:" + str(self.users_grid.children))
        connected_users = self.get_active_usernames()[1:-1].split(", ")
        print(f"connected users: {connected_users}")
        all_users = self.get_all_usernames()[1:-1].split(", ")
        disconnected_users = filter(
            lambda username: username not in connected_users, all_users)
        #self.enable = False
        #self.enable = True"""
        with self._connected_users_lock:
            connected_users = self._connected_users
        with self._all_users_lock:
            all_users = self._all_users
        disconnected_users = filter(
            lambda username: username not in connected_users, all_users)
        self.users_grid.clear_widgets()
        logging.debug("before child:" + str(self.users_grid.children))
        for username in connected_users:
            self.users_grid.rows += 1
            logging.debug(f"username: {username}")
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
            logging.debug(f"other username: {username}")
            self.users_grid.add_widget(Button(
                text=username,
                size_hint_y=None,
                height=40,
                on_press=self.select_username))
        logging.debug("after child:" + str(self.users_grid.children))

    def on_enter(self):
        self._connected_users = []
        self._all_users = []
        with self._get_users_lock:
            self._get_users = True
        self._app.connection_manager.add_connection("get users",
                                                    (True, True),
                                                    "main")
        self._get_users_thread = threading.Thread(target=self.get_users)
        self._get_users_thread.start()

    def on_pre_leave(self):
        logging.debug("starting to leave")
        with self._get_users_lock:
            self._get_users = False
        logging.debug("trying to close connection")
        self._get_users_thread.join()  # not good because it's io
        logging.warning("Trying to crash socket")
        try:
            self._app.connection_manager.close_connection("get users", True)
        except Exception as e:
            logging.error("socket error while closing: " + str(e))
        logging.debug("closed connection to get users")
