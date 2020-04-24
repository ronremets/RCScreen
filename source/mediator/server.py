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
from communication.message import Message, MESSAGE_TYPES, ENCODING
from communication.advanced_socket import AdvancedSocket
from communication.connection import Connection
from users_database import UsersDatabase
from token_generator import TokenGenerator

# TODO: Add a DNS request instead of static IP and port.
SERVER_ADDRESS = ("0.0.0.0", 2125)  # TODO: put it here or in main?
# TODO: Do we need timeout? Did we implement it all the way? How much to
#  set it
DEFAULT_REFRESH_RATE = 2


class Server(object):
    """
    Handles all communication between clients.
    """
    def __init__(self, db_file_name, refresh_rate=DEFAULT_REFRESH_RATE):
        self.refresh_rate = refresh_rate
        self._db_file_name = db_file_name
        self._server_socket = None
        self._users = None
        self._token_generator = TokenGenerator()
        self._accept_connections_thread = None
        self._running_lock = threading.Lock()
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

    def _run_connector(self, connection, user, db_connection):
        # Only connector type sockets use login and sign up and they do
        # not need the db_connection
        logging.info(f"CONNECTIONS:Started connector of {user.username}")
        db_connection.close()
        while self.running:
            name = connection.socket.recv().get_content_as_text()
            logging.debug(
                f"CONNECTIONS:Making token for {user.username}'s {name}")
            token = self._token_generator.generate(user.username,
                                                   name)
            logging.debug(
                f"CONNECTIONS:Made token {token} for {user.username}'s {name}")
            connection.socket.send(Message(
                MESSAGE_TYPES["server interaction"],
                "ok\n".encode(ENCODING) + token))

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

    def _send_messages_to_partner(self, partner_connection, buffer):
        """
        Send messages from a buffer to partner until connection closes
        TODO: make sure these threads close when connection closes
         and not when server closes (instead of while self.running use
         something like while not connection.is_closing or something
         like that)
        :param partner_connection: The connection of the partner
        :param buffer: A reference to the buffer of messages to send
        """
        can_send_message = True
        while self.running and partner_connection.running:
            message = buffer.pop()
            if (message is not None
                    and can_send_message
                    and partner_connection.connected):
                partner_connection.socket.send(message)
                can_send_message = False
            elif not can_send_message and partner_connection.connected:
                # Receive an ACK
                response = partner_connection.socket.recv(block=False)
                if response is not None:
                    can_send_message = True

    def _run_connection_to_partner(self, connection, user, buffered=False):
        """
        Run a connection that sends data to the partner of the user
        and are buffered.
        :param connection: The connection that sends data.
        :param user: The user of the connection.
        :param buffered: Whether to buffer between receiving from one
                         side and sending to the other. Decreases packet
                         drops but increases latency.
        """
        logging.info("starting main loop of connection to partner")
        buffer = MessageBuffer(buffered)
        while not user.partner.has_connection(connection.name):
            if not self.running:
                return  # TODO: maybe go into an error state
        partner_connection = user.partner.get_connection(connection.name)
        while not partner_connection.connected:
            if not self.running:
                return  # TODO: maybe go into an error state
        # TODO: maybe keep a reference to this thread to join it
        #  when closing the connection
        threading.Thread(name=(f"Connection to partner {connection.name} of"
                               f"User {user.username} to {user.partner}"),
                         target=self._send_messages_to_partner,
                         args=(connection, user, buffer)).start()
        while self.running and connection.running:
            # TODO: what if connections turns from connected to not
            #  connected? these if's have to handle this also close
            message = None
            if connection.connected:
                # Try to receive a message.
                message = connection.socket.recv(block=False)
            if message is not None:
                # If you did receive a message, add it to the buffer.
                buffer.add(message)
                # Finally, send an ACK to get another message.
                connection.socket.send(Message(
                    MESSAGE_TYPES["controlled"],
                    "Message received"))

    def _run_buffered_connection_to_partner(self, connection, user):
        """
        Run a connection that sends data to the partner of the user
        and is buffered.
        :param connection: The connection that sends data.
        :param user: The user of the connection.
        """
        logging.info("starting main loop of buffered connection to partner")
        # Wait for partner to create the connection.
        # TODO: partner can be None and this will crash
        while not user.partner.has_connection(connection.name):
            if not self.running:
                return  # TODO: maybe go into an error state
        partner_connection = user.partner.get_connection(connection.name)
        # Wait for partner to connect the connection.
        while not partner_connection.connected:
            if not self.running:
                return  # TODO: maybe go into an error state
        while self.running and connection.running:
            message = None
            if connection.connected:
                message = connection.socket.recv(block=False)
            if message is not None and partner_connection.connected:
                partner_connection.socket.send(message)

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
        #with self._connections_lock:
        #    self._connections.append(connection)

        #  the user will todo: go over this
        # be connected. If the user is not connected it must be because
        # it crashed or disconnected and thus crashing this connection
        # is fine.
        try:
            with self._users_lock:
                user = self._users[username]
        except KeyError:
            raise ValueError("User does not exists or disconnected")
        self._token_generator.release_token(token,
                                            user.username,
                                            connection.name)
        user.add_connection(connection)
        logging.debug(
            f"CONNECTIONS:Connection {connection.name} "
            f"added to {user.username}")
        return user

    def _validate_connector(self, username, password, database_connection):
        """
        Check whether the info given can be used to log in the
        user and its connector and return the verdict.
        :param username: The username of the user.
        :param password: The password of the user.
        :param database_connection: The connection to the database.
        :return: a string with the validation status.
        """
        try:
            if not database_connection.username_exists(username):
                return "username does not exists"
            elif password != database_connection.get_password(username):
                return "password is wrong"
            with self._users_lock:
                if username in self._users.keys():
                    return "user already connected"
        except ValueError as e:
            if e.args[0] == "No such user":
                logging.critical("UNREACHABLE CODE REACHED!!!!")
                return "username does not exists"
            raise
        return "user is valid"

    def _login(
            self,
            connection_socket,
            connection_info,
            database_connection=None):
        """
        Validate the user and add it to connected users
        :param connection_socket: The socket to login
        :param connection_info: info used to login
        :param database_connection: If available, a connection made in
                                    the same thread
        :return: Connection object and its user
        :raise IndexError: If some arguments are missing from
                           connection_info
        """
        username = connection_info[0]
        password = connection_info[1]
        connection_type = connection_info[2]
        connection_name = connection_info[3]
        try:
            if database_connection is None:
                # TODO: handle database errors in init and validate_connector
                database_connection = UsersDatabase(self._db_file_name)
            # TODO: add something like logging in here and errors and security
            validation_status = self._validate_connector(username,
                                                         password,
                                                         database_connection)
            if validation_status != "user is valid":
                raise ValueError(validation_status)
        except Exception:
            database_connection.close()
            raise

        connection = Connection(
            connection_name,
            connection_socket,
            connection_type)
        connection.start()  # TODO: is this fine? check the rest of the code

        # Remember that the user has to be connected to pass
        # self._validate_connector and thus is not connected yet.
        user = User(username, password, connection)
        with self._users_lock:
            self._users[username] = user
        # If the user has not yet connected, it must not have a
        # connector. Therefore add_connection cannot crash.
        user.add_connection(connection)
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

    def _connect_connection(self, connection_advanced_socket):
        """
        Connect a connection
        :param connection_advanced_socket: The advanced socket of the
                                           connection.
        :return: Connection object and its user object and its
                 connection to the database
        """
        connection_status = "ready"
        connecting_method = connection_advanced_socket.recv(
        ).get_content_as_text()
        logging.info("connecting method: " + connecting_method)
        connection_info = connection_advanced_socket.recv(
        ).get_content_as_text().split("\n")
        try:
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
        except ValueError as e:
            error_string = e.args[0]
            if error_string in ("username does not exists",
                                "password is wrong"):
                connection_status = "Username or password are wrong"
            elif error_string == "user already connected":
                connection_status = "User already connected"
            elif error_string == "Bad method":
                connection_status = "Connection method does not exists"
            else:
                connection_status = "Unknown server Error"
        except Exception:
            raise ValueError("Could not connect")
        connection_advanced_socket.send(Message(
            MESSAGE_TYPES["server interaction"],
            connection_status))
        # Make sure buffers are empty before switching
        response = connection_advanced_socket.recv(block=True)
        if connection_status != "ready":
            logging.debug(
                f"CONNECTIONS:Crashed with "
                f"connection status: {response.get_content_as_text()}")
            raise ValueError("could not connect")
        logging.debug(
            f"CONNECTIONS:{connection.name} "
            f"connection status: {response.get_content_as_text()}")
        return connection, user, db_connection

    def _run_main_loop_of_connection(self, connection, user, db_connection):
        """
        Based on the connection type, run its main loop.
        :param connection: The connection object.
        :param user: The user of the connection.
        :param db_connection: The connection to the database of the
                              connection.
        """
        logging.info(
            f"CONNECTIONS:Selecting main loop"
            f"for connection {connection.name}")
        if connection.type == "connector":
            connection.connected = True
            self._run_connector(connection, user, db_connection)
        elif connection.type == "main":
            connection.connected = True
            self._run_main(connection, user, db_connection)
        elif connection.type in ("keyboard - sender", "mouse - sender"):
            logging.info("connecting buffered sender socket")
            connection.socket.switch_state(True, True)
            # (Does not block) Senders do not need to receive any data.
            # Therefore, the server will never send to them data and
            # thus, their sending threads can be closed to conserve CPU
            # usage.
            logging.debug(
                f"closing send thread of connection {connection.name}")
            connection.socket.close_send_thread()
            connection.connected = True
            self._run_buffered_connection_to_partner(connection, user)
        elif connection.type in ("keyboard - receiver", "mouse - receiver"):
            logging.info("connecting buffered receiver socket")
            connection.socket.switch_state(True, True)
            # (Does not block) Receivers do not need to send any data.
            # Therefore, the server will never receive from them data
            # and thus, their receiving threads can be closed to conserve
            # CPU usage.
            logging.debug(f"closing recv thread of connection {connection.name}")
            connection.socket.close_recv_thread()
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
            raise ValueError("Connection type does not exists")

    def _run_connection(self, connection_socket):
        """
        run a connection to a client until the server closes
        :param connection_socket: the socket of the connection
        """
        connection_advanced_socket = AdvancedSocket()
        connection_advanced_socket.start(connection_socket, True, True)
        try:
            connection, user, db_connection = self._connect_connection(
                connection_advanced_socket)
        except ValueError as e:
            if e.args[0] == "could not connect":
                # TODO: maybe reconnect socket here
                pass
            #else:
            logging.error("SERVER:Socket error", exc_info=True)
            connection_advanced_socket.shutdown()
            connection_advanced_socket.close()
        except Exception:
            logging.error("SERVER:Socket error", exc_info=True)
            connection_advanced_socket.shutdown()
            connection_advanced_socket.close()
        else:
            # TODO: try except here
            self._run_main_loop_of_connection(connection, user, db_connection)

    def _accept_connections(self):
        """
        Accept and handle connections until server closes.
        """
        while self.running:
            try:
                connection_socket, addr = self._server_socket.accept()
                logging.info(f"New client: {addr}")
                threading.Thread(
                    name=f"Accept {addr} thread",
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
        self._server_socket = socket.socket()
        self._server_socket.settimeout(DEFAULT_REFRESH_RATE)
        self._server_socket.bind(SERVER_ADDRESS)
        self._server_socket.listen()  # TODO: Add parameter here.
        self._accept_connections_thread = threading.Thread(
            name="accept connections thread",
            target=self._accept_connections)
        self._set_running(True)
        self._accept_connections_thread.start()
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
