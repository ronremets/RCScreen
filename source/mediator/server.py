"""
Handles communication between the clients and the server
TODO: Add exception handling.
"""

__author__ = "Ron Remets"

import logging
import random
import socket
import threading
import time

from message_buffer import MessageBuffer
from mediator.user import User
from communication.message import Message, MESSAGE_TYPES
from communication.advanced_socket import AdvancedSocket
from communication.connection import Connection
from users_database import UsersDatabase

# TODO: Add a DNS request instead of static IP and port.
SERVER_ADDRESS = ("0.0.0.0", 2125)  # TODO: put it here or in main?
# TODO: Do we need timeout? Did we implement it all the way? How much to
#  set it
TIMEOUT = 2


class Server(object):
    """
    Handles all communication between clients.
    """
    def __init__(self, db_file_name):
        self._db_file_name = db_file_name
        self._server_socket = None
        self._connections = None
        self._users = None
        self._tokens_index = 0
        self._accept_connections_thread = None
        #self._remove_closed_connections_thread = None
        self._tokens_index_lock = threading.Lock()
        self._running_lock = threading.Lock()
        self._connections_lock = threading.Lock()
        self._users_lock = threading.Lock()
        self._set_running(False)

    @property
    def running(self):
        """
        :return: If the server is running.
        """
        with self._running_lock:
            return self._running

    def _set_running(self, value):
        with self._running_lock:
            self._running = value

    def _set_partner(self, connection, user, partner_username):
        """
        Set a user's partner.
        :param connection: The connection to the user
        :param user: The user
        :param partner_username: The username of the partner
        TODO: maybe return response code? Or response string?
        """
        partner_username = partner_username
        with self._users_lock:
            user.partner = self._users[partner_username]
        connection.socket.send(Message(
            MESSAGE_TYPES["server interaction"],
            "set partner"))
        logging.info("set partner to: " + str(partner_username))

    def _get_all_usernames(self, connection, db_connection):
        """
        Send all usernames to a user
        :param connection: The connection to the user
        :param db_connection: The connection to the database
        """
        a = db_connection.get_all_usernames()
        logging.debug(f"MAIN SERVER:Sending all usernames: {a}")
        connection.socket.send(Message(
            MESSAGE_TYPES["server interaction"],
            ", ".join(a)))

    def _get_all_connected_usernames(self, connection):
        """
        Send a user all connected users.
        :param connection: The connection to the user
        """
        with self._users_lock:
            usernames = [*self._users.keys()]
        formatted_response = ", ".join(usernames)
        connection.socket.send(Message(
            MESSAGE_TYPES["server interaction"],
            formatted_response))

    def make_token(self):
        """
        Create a random token for connection
        :return: A bytes object with the token
        """
        with self._tokens_index_lock:
            self._tokens_index += 11
            return (str(int(time.time()) ^ random.randint(1000, 9999))
                    + str(self._tokens_index)).encode("ascii")

    def _run_connector(self, connection, user, db_connection):
        # Only connector type sockets use login and sign up and they do
        # not need the db_connection
        logging.info(f"CONNECTIONS:Started connector of {user.username}")
        db_connection.close()
        while self.running:
            # TODO: check name and token match
            name = connection.socket.recv().get_content_as_text()
            logging.debug(
                f"CONNECTIONS:Making token for {user.username}'s {name}")
            token = self.make_token()
            logging.debug(
                f"CONNECTIONS:Made token {token} for  {user.username}'s {name}")
            user.add_token(token, name)
            connection.socket.send(Message(
                MESSAGE_TYPES["server interaction"],
                f"ok\n{token.decode()}"))  # TODO: you should not have to decode

    def _run_main(self, connection, user, db_connection):
        while self.running:
            params = connection.socket.recv().get_content_as_text().split("\n")
            if params[0] == "set partner":
                self._set_partner(connection, user, params[1])
            elif params[0] == "get all usernames":
                self._get_all_usernames(connection, db_connection)
            elif params[0] == "get all connected usernames":
                self._get_all_connected_usernames(connection)
            else:
                pass  # TODO: Add errors here
            # TODO: Add more commands like closing other connections of
            #  this user and closing all connections and deleting the
            #  user and more

    def _send_messages_to_partner(self, connection, user, buffer):
        """
        Send messages from a buffer to partner until connection closes
        TODO: make sure these threads close when connection closes
         and not when server closes (instead of while self.running use
         something like while not connection.is_closing or something
         like that)
        :param connection: The connection to use to find the partner's
                           connection
        :param user: The user sending the messages
        :param buffer: A reference to the buffer of messages to send
        """
        while self.running:  # TODO: not self.running but connection.running
            if connection.name in user.partner.connections:
                if user.partner.connections[connection.name].connected:
                    message = buffer.pop()
                    if message is not None:
                        user.partner.connections[connection.name].socket.send(
                            Message(MESSAGE_TYPES["controller"],
                                    message))
                        # Receive an ACK
                        user.partner.connections[connection.name].socket.recv()

    def _run_connection_to_partner(self, connection, user, buffered=False):
        logging.info("starting main loop of connection to partner")
        buffer = MessageBuffer(buffered)
        # TODO: maybe keep a reference to this thread to join it
        #  when closing the connection
        threading.Thread(target=self._send_messages_to_partner,
                         args=(connection, user, buffer)).start()
        while self.running:
            # TODO: what if connections turns from connected to not
            #  connected? these if's have to handle this
            if connection.name in user.partner.connections:
                # TODO: what if connections are removed here from dict?
                if user.partner.connections[connection.name].connected:
                    message = connection.socket.recv(block=False)
                    if message is not None:
                        buffer.add(message.content)
                        # Send an ACK
                        connection.socket.send(Message(
                            MESSAGE_TYPES["controlled"],
                            "Message received"))

    def _add_connection_to_user(self, connection, username, token):
        """
        Add a connection to a user, user must be connected and have a
        connector
        :param connection: The connection to add
        :param username: The user's username
        :param token: The token of the user used to connect to the user
        :return: The user's object
        :raise ValueError: If token does not exists or belong
                           to connection or if the user does not exists
        """
        with self._connections_lock:
            self._connections.append(connection)

        # A new connection can not get to here without a token in user
        # therefore it is safe to assume it exists. Also, the user will
        # be connected. If the user is not connected it must be because
        # it crashed or disconnected and thus crashing this connection
        # is fine.
        try:
            with self._users_lock:
                user = self._users[username]
        except KeyError:
            raise ValueError("User does not exists or disconnected")
        user.validate_token(token, connection.name)
        user.add_connection(connection)
        logging.debug(
            f"CONNECTIONS:Connection {connection.name} "
            f"added to {user.username}")
        return user

    def _add_connector_to_user(self, connection, username, password):
        """
        Add a connector to a user using username and password
        :param connection: The connector connection
        :param username: The username of the user
        :param password: The password of the user
        :return: The user's object
        """
        with self._connections_lock:
            self._connections.append(connection)

        with self._users_lock:
            if username in self._users.keys():
                raise ValueError("User already connected")
            user = User(username, password, connection)
            self._users[username] = user
        # TODO: ensure locking user.connections.connections to
        #  prevent data corruption. While the pointer is locked the
        #  dict is not
        logging.debug(
            f"CONNECTIONS:Connection {connection.name} "
            f"added to {user.username}")
        user.connections[connection.name] = connection
        return user

    def _login(
            self,
            connection_socket,
            connection_info,
            database_connection=None):
        """
        Login a socket
        :param connection_socket: The socket to login
        :param connection_info: info used to login
        :param database_connection: If available, a connection made in
                                    the same thread
        :return: Connection object and its user
        """
        username = connection_info[0]
        password = connection_info[1]
        connection_type = connection_info[2]
        connection_name = connection_info[3]
        if database_connection is None:
            database_connection = UsersDatabase(self._db_file_name)
        # TODO: add something like logging in here and errors and security
        logging.info(database_connection.get_user(username, password))
        connection = Connection(
            connection_name,
            connection_socket,
            connection_type)
        connection.start()  # TODO: is this fine? check the rest of the code
        user = self._add_connector_to_user(
            connection,
            username,
            password)
        return connection, user, database_connection

    def _signup(self, connection_socket, connection_info):
        username = connection_info[0]
        password = connection_info[1]
        database_connection = UsersDatabase(self._db_file_name)
        # TODO: add something like logging in here
        database_connection.add_user(username, password)
        return self._login(
            connection_socket,
            connection_info,
            database_connection=database_connection)

    def _connect_with_token(self,
                            connection_socket,
                            connection_info):
        username = connection_info[0]
        token = connection_info[1].encode("ascii") # TODO: encode everything else instead of decode this
        connection_type = connection_info[2]
        connection_name = connection_info[3]
        # TODO: add something like logging in here and errors and security
        # TODO: get token
        connection = Connection(
            connection_name,
            connection_socket,
            connection_type)
        # TODO: elsewhere in the code make sure you check that the
        #  connection starts before you check if it is closed
        connection.start()  # TODO: is this fine? check the rest of the code
        user = self._add_connection_to_user(
            connection,
            username,
            token)
        return connection, user

    def _create_connection(self, connection_socket):
        """
        Create a connection
        :param connection_socket: The socket of the connection.
        :return: Connection object and its user object
        """
        # TODO: replace the address default parameter with a parameter
        #  that tells the socket to not create a new socket
        connection_advanced_socket = AdvancedSocket()
        connection_advanced_socket.start(True, True, connection_socket)
        # TODO: maybe connect both recv to one. remember that some
        #  methods might not work in one recv
        connecting_method = connection_advanced_socket.recv(
            ).get_content_as_text()
        logging.info("connecting method: " + connecting_method)
        connection_info = connection_advanced_socket.recv(
            ).get_content_as_text().split("\n")
        if connecting_method == "login":
            connection, user, db_connection = self._login(
                connection_advanced_socket,
                connection_info)
        elif connecting_method == "signup":
            connection, user, db_connection = self._signup(
                connection_advanced_socket,
                connection_info)
        elif connecting_method == "token":
            connection, user = self._connect_with_token(
                connection_advanced_socket,
                connection_info)
            db_connection = UsersDatabase(self._db_file_name)
        else:
            raise ValueError("Bad method")

        connection.socket.send(Message(
            MESSAGE_TYPES["server interaction"],
            "ready"))
        if connection.name != "connector":
            # Make sure buffers are empty before switching
            response = connection.socket.recv(block=True)
            logging.debug(
                f"CONNECTIONS:{connection.name} "
                f"connection status: {response.get_content_as_text()}")
        return connection, user, db_connection

    def _run_connection(self, connection_socket):
        """
        run a connection to a client until the server closes
        :param connection_socket: the socket of the connection
        """
        connection, user, db_connection = self._create_connection(
            connection_socket)
        logging.info(
            f"CONNECTIONS:Selecting main loop"
            f"for connection {connection.name}")
        # TODO: fix: getpeerbyname might not be supported on all systems
        if connection.type == "connector":
            connection.connected = True
            self._run_connector(connection, user, db_connection)
        elif connection.type == "main":
            connection.connected = True
            self._run_main(connection, user, db_connection)
        elif connection.type in ("keyboard - sender", "mouse - sender"):
            logging.info("connecting buffered sender socket")
            connection.socket.switch_state(True, True)
            connection.connected = True
            self._run_connection_to_partner(connection, user, buffered=True)
        elif connection.type in ("keyboard - receiver", "mouse - receiver"):
            logging.info("connecting buffered receiver socket")
            connection.socket.switch_state(True, True)
            connection.connected = True
            db_connection.close()
        elif connection.type == "frame - sender":
            logging.info("connecting unbuffered sender socket")
            connection.socket.switch_state(False, True)
            connection.connected = True
            self._run_connection_to_partner(connection, user)
        elif connection.type == "frame - receiver":
            logging.info("connecting unbuffered receiver socket")
            connection.socket.switch_state(True, False)
            connection.connected = True
            db_connection.close()
        else:
            raise ValueError("type does not exists")

    def _accept_connections(self):
        """
        Accept and handle connections until server closes.
        """
        while self.running:  # TODO: add timeout
            try:
                connection_socket, addr = self._server_socket.accept()
                logging.info(f"New client: {addr}")
                threading.Thread(
                    target=self._run_connection,
                    args=(connection_socket,)).start()
            except socket.timeout:
                pass

    #def _remove_closed_connections(self):
        """
        Remove closed connections from the list of connections until
        the server closes.
        """
        # TODO: Rethink this. Is it necessary? Any faster way of doing
        #  this?
    #    while self.running:
    #        with self._connections_lock:
                # Create a shallow copy of the list because of the
                # for loop.
    #            for connection in self._connections[:]:
    #                if not connection.running:
    #                    self._connections.remove(connection)

    def start(self):
        """
        Start the server.
        """
        self._users = {}
        self._connections = []
        self._server_socket = socket.socket()
        self._server_socket.settimeout(TIMEOUT)
        self._server_socket.bind(SERVER_ADDRESS)
        self._server_socket.listen()  # TODO: Add parameter here.
        self._accept_connections_thread = threading.Thread(
            target=self._accept_connections)
        #self._remove_closed_connections_thread = threading.Thread(
        #    target=self._remove_closed_connections)
        self._set_running(True)
        self._accept_connections_thread.start()
        #self._remove_closed_connections_thread.start()
        logging.info("done starting server")

    def close(self, timeout=None):
        """
        Close the server.
        :param timeout: If not None, the amount of seconds to wait
                        when closing
        """
        self._set_running(False)
        self._connect_connections_thread.join(timeout)
        #self._remove_closed_connections_thread.join()
        # TODO: Make sure all connections are closed before calling close
        #  on server socket
        self._server_socket.close()
