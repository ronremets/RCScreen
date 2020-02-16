"""
Handles communication between the clients and the server
TODO: Add exception handling.
"""

__author__ = "Ron Remets"

import socket
import threading

from mediator.user import User
from communication.message import Message, MESSAGE_TYPES
from communication import communication_protocol
from communication.advanced_socket import AdvancedSocket
from connection import Connection
from data.users_database import UsersDatabase

# TODO: Add a DNS request instead of static IP and port.
SERVER_ADDRESS = ("0.0.0.0", 2125)  # TODO: put it here or in main?
# TODO: Do we need timeout? Did we implement it all the way? How much to
#  it
TIMEOUT = 2


class Server(object):
    """
    Handles all communication between clients.
    """
    def __init__(self):
        self._server_socket = None
        self._connections = None
        self._users = None
        self._users_database = None
        self._connect_connections_thread = None
        self._remove_closed_connections_thread = None
        self._running_lock = threading.Lock()
        self._connections_lock = threading.Lock()
        self._users_database_lock = threading.Lock()
        self._users_lock = threading.Lock()
        self._set_running(False)

    @property
    def running(self):
        """
        :return: If the server is running.
        """
        with self._running_lock:
            return self.__running

    def _set_running(self, value):
        with self._running_lock:
            self.__running = value

    def _run_main(self, connection, user):
        while self.running:
            # TODO: add parameters to the protocol to make it more clear
            #  for example: "fixed_length_header|param_name = value\n
            #  like http protocol
            params = connection.socket.recv().get_content_as_text().split("\n")
            if params[0] == "set partner":
                partner_username = params[1]
                with self._users_lock:
                    user.partner = self._users[partner_username]
            elif params[0] == "get all usernames":
                connection.send(Message(
                    MESSAGE_TYPES["server interaction"],
                    self._users_database.get_all_usernames()))
            else:
                pass  # TODO: Add errors here
            # TODO: Add more commands like closing other connections of
            #  this user and closing all connections and deleting the
            #  user and more

    def _run_buffered(self, connection, user):
        while self.running:
            user.partner.socket.send(Message(
                MESSAGE_TYPES["controller"],
                connection.socket.recv().encode(
                    communication_protocol.ENCODING)))

    def _run_unbuffered(self, connection, user):
        while self.running:
            user.partner.socket.send(Message(
                MESSAGE_TYPES["controlled"],
                connection.socket.recv().encode(
                    communication_protocol.ENCODING)))

    def _join_connection(self, connection, username, password):
        with self._connections_lock:
            self._connections.append(connection)

        with self._users_lock:
            if username in self._users:  # TODO: Maybe .keys() ?
                user = self._users[username]
                user.connections.append(connection)
            else:
                user = User(username, password)
                user.connections.append(connection)
                self._users[username] = user
        return user

    def _login(self, connection_socket, connection_info):
        """
        Login a socket
        :param connection_socket: The socket to login
        :param connection_info: info used to login
        :return: Connection object and its user
        """
        username = connection_info[0]
        password = connection_info[1]
        # TODO: add something like logging in here
        self._users_database.get_user(username, password)
        connection_type = connection_info[2]
        connection = Connection(connection_socket, connection_type)
        user = self._join_connection(connection, username, password)
        return connection, user

    def _signup(self, connection_socket, connection_info):
        username = connection_info[0]
        password = connection_info[1]
        # TODO: add something like logging in here
        self._users_database.add_user(username, password)
        return self._login(connection_socket, connection_info)

    def _create_connection(self, connection_socket):
        """
        Create a connection
        :param connection_socket: The socket of the connection.
        :return: Connection object and its user object
        """
        connection_advanced_socket = AdvancedSocket()
        connection_advanced_socket.start(True, True, connection_socket)
        connecting_method = connection_advanced_socket.recv(
            ).get_content_as_text()
        print("cm:" + connecting_method)
        connection_info = connection_advanced_socket.recv(
            ).get_content_as_text().split("\n")
        if connecting_method == "login":
            connection, user = self._login(
                connection_advanced_socket,
                connection_info)
        elif connecting_method == "signup":
            connection, user = self._signup(
                connection_advanced_socket,
                connection_info)
        else:
            raise ValueError("Bad method")
        connection.socket.send(Message(
            MESSAGE_TYPES["server interaction"],
            "Connected".encode(communication_protocol.ENCODING)))
        return connection, user

    def _run_connection(self, connection_socket):
        """
        run a connection to a client until the server closes
        :param connection_socket: the socket of the connection
        """
        connection, user = self._create_connection(connection_socket)
        # TODO: fix: getpeerbyname might not be supported on all systems
        if connection.type == "main":
            self._run_main(connection, user)
        elif connection.type in ("frame", "sound", "mouse move"):
            connection.socket.switch_state(False, True)
            self._run_unbuffered(connection, user)
        elif connection.type in ("keyboard", "mouse button"):
            connection.socket.switch_state(True, False)
            self._run_buffered(connection, user)
        connection.close()

    def _connect_connections(self):
        """
        Connect connections until server closes.
        """
        while self.running:
            try:
                connection_socket, addr = self._server_socket.accept()
                # TODO: Remove and replace with logging.
                print(f"New client: {addr}")
                threading.Thread(
                    target=self._run_connection,
                    args=(connection_socket,)).start()
            except socket.timeout:
                pass

    def _remove_closed_connections(self):
        """
        Remove closed connections from the list of connections until
        the server closes.
        """
        # TODO: Rethink this. Is it necessary? Any faster way of doing
        #  this?
        while self.running:
            with self._connections_lock:
                # Create a shallow copy of the list because of the
                # for loop.
                for connection in self._connections[:]:
                    if not connection.running:
                        self._connections.remove(connection)

    def start(self):
        """
        Start the server.
        """
        # maybe use a dict like {user:client}
        self._users = {}
        self._connections = []
        self._users_database = UsersDatabase("users.db")
        self._server_socket = socket.socket()
        self._server_socket.settimeout(TIMEOUT)
        self._server_socket.bind(SERVER_ADDRESS)
        self._server_socket.listen()  # TODO: Add parameter here.
        self._connect_connections_thread = threading.Thread(
            target=self._connect_connections)
        self._remove_closed_connections_thread = threading.Thread(
            target=self._remove_closed_connections)
        self._set_running(True)
        self._connect_connections_thread.start()
        self._remove_closed_connections_thread.start()

    def close(self, block=True):
        """
        Close the server.
        :param block: (When True) - Wait for all threads to finish
                      before closing which results in a smoother close.
        """
        self._set_running(False)
        if block:
            self._connect_connections_thread.join()
            self._remove_closed_connections_thread.join()
        # TODO: Make sure all connections are closed before calling close
        #  on server socket
        self._server_socket.close()
