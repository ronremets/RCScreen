"""
Handles communication between the clients and the server
TODO: Add exception handling.
"""

__author__ = "Ron Remets"

import enum
import logging
import socket
import threading
import time
import ssl
import queue

from communication.message_buffer import MessageBuffer
from communication.user import User
from communication.client import Client
from communication.message import Message, MESSAGE_TYPES, ENCODING
from communication import advanced_socket  # TODO: ?????? why
from communication.advanced_socket import AdvancedSocket
from communication.connection import Connection, ConnectionStatus
from users_database import UsersDatabase
from token_generator import TokenGenerator
from communication.connector import Connector

# TODO: Add a DNS request instead of static IP and port.
DEFAULT_SERVER_ADDRESS = ("0.0.0.0", 2125)
# TODO: Do we need timeout? Did we implement it all the way? How much to
#  set it
DEFAULT_REFRESH_RATE = 2
DEFAULT_DB_FILENAME = 'users.db'
context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.VerifyMode.CERT_NONE
context.load_cert_chain('./cert/server.pem', './cert/server.key')


class DisconnectReason(enum.Enum):
    """
    Reasons for the main loop of a client to close
    """
    CONNECTION_DISCONNECT = enum.auto()
    CLIENT_DISCONNECT = enum.auto()
    PARTNER_CONNECTION_DISCONNECT = enum.auto()
    PARTNER_DISCONNECT = enum.auto()
    SERVER_CLOSE = enum.auto()


class DisconnectedError(Exception):
    """
    Base class for the disconnections exceptions
    """
    pass


class ConnectionDisconnectedError(DisconnectedError):
    """
    Occurs if the connection disconnects while running
    """
    pass


class ClientDisconnectedError(DisconnectedError):
    """
    Occurs if the client disconnects while running
    """
    pass


class PartnerDisconnectedError(DisconnectedError):
    """
    Occurs if the partner of the connection disconnects while running
    """
    pass


class PartnerConnectionDisconnectedError(DisconnectedError):
    """
    Occurs if the connection of the partner disconnects while running
    """
    pass


class ServerDisconnectedError(DisconnectedError):
    """
    Occurs if the server disconnects while running
    """
    pass


# TODO: make sure all connections loops break when
#  ConnectionStatus is not CONNECTED
# TODO: make sure clients set DISCONNECTED when outside the loop
# TODO: make sure clients set CLOSED when their thread is done
# TODO: make every connection have its loop in its thread
#  and share a buffer instead
# TODO: what if connector has ERROR while closing?
# TODO: server close - close now, server shutdown - tell connector to
#  close everything
#  server crash - kill everything

# TODO: remember that Message().get_content_as_text()
#  can raise UnicodeDecodeError!


class Server(object):
    """
    Handles all communication between clients.
    """
    def __init__(self):
        self._db_file_name = None
        self._server_socket = None
        self._clients = None
        self._token_generator = TokenGenerator()
        self._accept_connections_thread = None
        self._running_lock = threading.Lock()
        self._clients_lock = threading.Lock()
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

    def _set_partner(self, connection, client, partner_username):
        """
        Set a client's partner.
        :param connection: The connection to the user
        :param client: The client
        :param partner_username: The username of the partner
        TODO: maybe return response code? Or response string?
        """
        # TODO: close all connections to partner before switching
        with self._clients_lock:
            client.partner = self._clients[partner_username]
        connection.socket.send(Message(
            MESSAGE_TYPES["server interaction"],
            "set partner"))
        logging.info(f"set partner to: partner_username")

    def _get_all_usernames(self, connection, db_connection):
        """
        Send all usernames to a user
        :param connection: The connection to the user
        :param db_connection: The connection to the database
        """
        print(self.running)
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
        with self._clients_lock:
            usernames = [*self._clients.keys()]
        formatted_response = ", ".join(usernames)
        connection.socket.send(Message(
            MESSAGE_TYPES["server interaction"],
            formatted_response))

    def _generate_token(self, name, connection, client):
        """
        Create a token and send it to the client.
        :param name: The name of the connection to create the token for
        :param connection: The connector's connection
        :param client: the client of the connection
        """
        logging.debug(
            f"CONNECTIONS:Making token for "
            f"{client.user.username}'s {name}")
        token = self._token_generator.generate(client.user.username,
                                               name)
        logging.debug(
            f"CONNECTIONS:Made token {token} "
            f"for {client.user.username}'s {name}")
        connection.socket.send(Message(
            MESSAGE_TYPES["server interaction"],
            "ok\n".encode(ENCODING) + token))

    def _disconnect_client(self, client, server_side):
        """
        Disconnect the client by closing all of its connections and
        removing him from the list of clients.
        :param client: The client to disconnect
        :param server_side: whether the disconnect was initiated in the
                            server or in the client
        """
        try:
            client.connector_close_all_connections(server_side)
        finally:
            with self._clients_lock:
                self._clients.remove(client)

    def _handle_connector_command(self,
                                  connector,
                                  client,
                                  command,
                                  from_queue):
        """
        Execute connector command
        :param connector: The connector connection
        :param client: The client of the connector
        :param command: The command to execute
        :param from_queue: Whether the command came from the connector's
                           queue or from the connector socket
        """
        try:
            instruction, name = Connector.parse_connector_command(command)
        except ValueError:
            logging.error(f"CONNECTOR:client {client.usern.username} did not"
                          "provide the required ':' in his connector command")
            raise ValueError("Missing the name part of the command")
        if instruction == "close":
            client.connector_close_connection(name, from_queue)
        elif instruction == "generate token":
            self._generate_token(name, connector, client)
        elif instruction == "disconnect":
            self._disconnect_client(client, from_queue)
        else:
            logging.error(f"CONNECTOR:client {client.usern.username} sent a"
                          f"command: {command} to connector that does not "
                          "exist")
            raise ValueError("Not a command")

    def _run_connector(self, connector, client, db_connection):
        """
        The main loop of the connector, it will receive commands from
        its queue and from the socket and handle them.
        :param connector: The connection of the connector
        :param client: The client of the connector
        :param db_connection: The connection to the database of the
                              connector
        """
        logging.info(f"CONNECTIONS:Started connector"
                     f" of {client.user.username}")
        db_connection.close()
        try:
            while True:
                if not self.running:
                    break
                elif connector.status is not ConnectionStatus.CONNECTED:
                    break
                time.sleep(0)  # Release GIL
                message = connector.socket.recv(block=False)
                if message is not None:
                    command = message.get_content_as_text()
                    self._handle_connector_command(connector,
                                                   client,
                                                   command,
                                                   False)
                time.sleep(0)  # Release GIL
                try:
                    command = connector.commands.get(block=False)
                except queue.Empty:
                    pass
                else:
                    self._handle_connector_command(connector,
                                                   client,
                                                   command,
                                                   True)
        except ValueError as e:
            connector.status = ConnectionStatus.DISCONNECTING
            if e.args[0] == "Not a command":
                logging.error(
                    "CONNECTIONS:Client sent connector unknown command")
            else:
                logging.error("CONNECTIONS:Connector error", exc_info=True)
        except Exception as e:
            print(e)
            logging.error("CONNECTIONS:Connector error", exc_info=True)
        finally:
            client.stop_adding_connections()
            connector.status = ConnectionStatus.DISCONNECTING
            while True:
                time.sleep(0)
                pass

    def _run_main(self, connection, client, db_connection):
        while True:
            time.sleep(0)  # Release GIL
            if connection.status is not ConnectionStatus.CONNECTED:
                raise ConnectionDisconnectedError()
            elif not self.running:
                raise ServerDisconnectedError()

            message = connection.socket.recv(block=False)
            if message is None:
                continue
            params = message.get_content_as_text().split("\n")
            if params[0] == "set partner":
                self._set_partner(connection, client, params[1])
            elif params[0] == "get all usernames":
                self._get_all_usernames(connection, db_connection)
            elif params[0] == "get all connected usernames":
                self._get_all_connected_usernames(connection)
            else:
                raise ValueError("No such command")
            # TODO: Delete user and more

    def _wait_for_partner_create_connection(self, connection, client):
        """
        Wait until partner creates a connection
        :param connection: The connection that will connect to the
                           partner.
        :param client: The client of the connection
        :raise ConnectionDisconnectedError: If connection disconnects
        :raise ServerDisconnectedError: If server disconnects
        :raise ValueError: on Error
        """
        try:
            while True:
                time.sleep(0)  # Release GIL
                # TODO: if client dies ConnectionStatus = error
                if connection.status is not ConnectionStatus.CONNECTED:
                    raise ConnectionDisconnectedError()
                elif not self.running:
                    raise ServerDisconnectedError()
                elif client.partner.has_connection(connection.name):
                    return
        except AttributeError:
            connection.status = ConnectionStatus.ERROR
            raise ValueError("Partner was not set or disconnected")

    def _wait_for_partner_connect_connection(self,
                                             connection,
                                             partner_connection):
        """
        Wait until partner connects a connection
        :param connection: The connection that will connect to the
                           partner.
        :param partner_connection: The connection of the partner that
                                   needs to connect.
        :raise ConnectionDisconnectedError: If connection disconnects
        :raise PartnerConnectionDisconnectedError: If the partner's
                                                   connection
                                                   disconnects
        :raise ServerDisconnectedError: If server disconnects
        """
        while True:
            time.sleep(0)  # Release GIL
            if connection.status is not ConnectionStatus.CONNECTED:
                raise ConnectionDisconnectedError()
            elif partner_connection.status is ConnectionStatus.DISCONNECTING:
                raise PartnerConnectionDisconnectedError()
            elif not self.running:
                raise ServerDisconnectedError()
            elif partner_connection.status is ConnectionStatus.CONNECTED:
                return

    def get_partner_connection(self, connection, client):
        """
        Wait until the partner creates and connects his connection
        and return that connection
        :param connection: The connection that will connect to the
                           partner
        :param client: The client of the connection
        :return: The partners connection
        :raise ValueError: on error
        :raise DisconnectError: (raises a subclass) if the client,
                                partner or server disconnects
        """
        self._wait_for_partner_create_connection(connection, client)

        try:
            partner_connection = client.partner.get_connection(connection.name)
        except KeyError:
            # Since you cannot set partner without closing all
            # connections that are connected to the partner, we can
            # assume that partner cannot change while this code is
            # running. I.E, if partner has a connection with the right
            # name, he must have it now because you cannot switch to
            # a partner that does not have the connection

            # Getting partner's connection from client.partner failed
            connection.status = ConnectionStatus.ERROR
            raise ValueError("Partner connection does not exists")
        except AttributeError:
            connection.status = ConnectionStatus.ERROR
            raise ValueError("Partner disconnected")

        self._wait_for_partner_connect_connection(connection,
                                                  partner_connection)
        return partner_connection

    def _send_messages_to_partner(self, partner_connection, buffer):
        """
        Send messages from a buffer to partner until connection closes
        :param partner_connection: The connection of the partner
        :param buffer: A reference to the buffer of messages to send
        """
        can_send_message = True
        try:
            while True:
                time.sleep(0)  # Release GIL
                # On close, this thread should just end since it is the
                # responsibility of the client to disconnect its partner
                if partner_connection.status is not ConnectionStatus.CONNECTED:
                    break
                elif not self.running:
                    break

                message = buffer.pop()
                if message is not None and can_send_message:
                    partner_connection.socket.send(message)
                    can_send_message = False
                elif not can_send_message:
                    # Receive an ACK
                    response = partner_connection.socket.recv(block=False)
                    if response is not None:
                        can_send_message = True
        except OSError:
            partner_connection.status = ConnectionStatus.DISCONNECTING
            logging.error(f"OSError while running"
                          f" partner connection {partner_connection.name}",
                          exc_info=True)
        except Exception as e:
            print(e)
            partner_connection.status = ConnectionStatus.DISCONNECTING
            logging.error(f"Unknown error while running"
                          f" partner connection {partner_connection.name}",
                          exc_info=True)

    def _run_connection_to_partner(self, connection, client):
        """
        Run a connection that sends data to the partner of the client
        and are buffered.
        :param connection: The connection that sends data.
        :param client: The client of the connection.
        :raise DisconnectError: (raises a subclass) if the client,
                                partner or server disconnects
        :raise ValueError: if cant connect to the partner
        """
        logging.info("starting main loop of connection to partner")
        buffer = MessageBuffer(False)

        partner_connection = self.get_partner_connection(connection, client)

        # TODO: maybe keep a reference to this thread to join it
        #  when closing the connection
        partner_thread = threading.Thread(
            name=(f"Connection to partner {connection.name} of "
                  f"User {client.user.username} to "
                  f"{client.partner.user.username}"),
            target=self._send_messages_to_partner,
            args=(partner_connection, buffer))
        partner_thread.start()

        try:
            while True:
                time.sleep(0)  # Release GIL
                if partner_connection.status is ConnectionStatus.DISCONNECTING:
                    raise PartnerConnectionDisconnectedError()
                elif connection.status is ConnectionStatus.DISCONNECTING:
                    raise ConnectionDisconnectedError()
                elif not self.running:
                    raise ServerDisconnectedError()

                # Try to receive a message.
                message = connection.socket.recv(block=False)
                if message is not None:
                    # If you did receive a message, add it to the buffer.
                    buffer.add(message)
                    # Finally, send an ACK to get another message.
                    connection.socket.send(Message(
                        MESSAGE_TYPES["controlled"],
                        "Message received"))
        except ConnectionDisconnectedError:
            partner_connection.status = ConnectionStatus.DISCONNECTING
            raise
        finally:
            partner_thread.join()

    def _run_buffered_connection_to_partner(self, connection, client):
        """
        Run a connection that sends data to the partner of the client
        and is buffered.
        :param connection: The connection that sends data.
        :param client: The client of the connection.
        :raise DisconnectError: (raises a subclass) if the client,
                                partner or server disconnects
        :raise ValueError: if cant connect to the partner
        """
        logging.info(
            f"starting main loop of buffered "
            f"connection {connection.name} to partner")

        partner_connection = self.get_partner_connection(connection, client)
        logging.debug(f"Got connection {partner_connection.name} of "
                      f"partner of {client.user.username}")
        while True:
            time.sleep(0)  # Release GIL
            if partner_connection.status is not ConnectionStatus.CONNECTED:
                raise PartnerConnectionDisconnectedError()
            elif connection.status is not ConnectionStatus.CONNECTED:
                raise ConnectionDisconnectedError()
            elif not self.running:
                raise ServerDisconnectedError()
            message = connection.socket.recv(block=False)
            if message is not None:
                partner_connection.socket.send(message)

    def _get_client(self, connection_name, username, token):
        """
        Get the client of a connection.
        :param connection_name: the name of the connection
        :param username: The username of the client.
        :param token: The token of the connection
        :return: The client object
        """
        try:
            with self._clients_lock:
                client = self._clients[username]
        except KeyError:
            raise ValueError("User does not exists or disconnected")
        # TODO: make sure token gets released even on crash
        self._token_generator.release_token(token,
                                            client.user.username,
                                            connection_name)
        return client

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
            with self._clients_lock:
                if username in self._clients.keys():
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
        Validate the information tha client gave, and add the client to
        the connected clients.
        :param connection_socket: The socket to login.
        :param connection_info: info used to login.
        :param database_connection: If available, a connection made in
                                    the same thread.
        :return: Connection object and its client.
        :raise ValueError: On any connection error.
        """
        try:
            username = connection_info[0]
            password = connection_info[1]
            connection_type = connection_info[2]
            connection_name = connection_info[3]
        except IndexError:  # TODO: combine both tries and excepts to one
            raise ValueError("Not enough connection info parameters")
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
            # TODO: what if database_connection is not None but cannot
            #  be closed?
            if database_connection is not None:
                database_connection.close()
            raise

        connection = Connector(
            connection_name,
            connection_socket,
            connection_type)
        connection.status = ConnectionStatus.CONNECTING
        # connection.start()  # TODO: is this fine? check the rest of the code
        user = User(username, password)

        # Remember that the client has to not be connected to pass
        # self._validate_connector and thus is not yet connected.
        client = Client(user)
        with self._clients_lock:
            self._clients[username] = client
        # If the client has not yet connected, it must not have a
        # connector. Therefore add_connection cannot crash.
        client.add_connection(connection)
        return connection, client, database_connection

    def _signup(self, connection_socket, connection_info):
        """
        Adds a user to server then connects the connection.
        :param connection_socket: The socket of the connection.
        :param connection_info: The information of the connection needed
                                to add the user and connect the
                                connection.
        :return: The connection, its client and its database connection.
        :raise ValueError: On any connection error.
        """
        try:
            username = connection_info[0]
            password = connection_info[1]
        except IndexError:  # TODO: combine both tries and excepts to one
            raise ValueError("Not enough connection info parameters")
        database_connection = UsersDatabase(self._db_file_name)
        # TODO: add something like logging in here
        try:
            database_connection.add_user(username, password)
        except Exception:
            database_connection.close()
            raise
        return self._login(
            connection_socket,
            connection_info,
            database_connection=database_connection)

    def _connect_with_token(self,
                            connection_socket,
                            connection_info):
        """
        Add a connection and connect it using a token.
        :param connection_socket: The socket of the connection.
        :param connection_info: info used to login (with a token)
        :return: The connection, its client and its database connection.
        """
        try:
            username = connection_info[0]
            # TODO: encode everything else instead of decode this
            token = connection_info[1].encode("ascii")
            connection_type = connection_info[2]
            connection_name = connection_info[3]
        except IndexError:
            raise ValueError("Not enough connection info parameters")
        # TODO: add something like logging in here and errors and security
        connection = Connection(
            connection_name,
            connection_socket,
            connection_type)
        connection.start()  # TODO: is this fine? check the rest of the code
        database_connection = UsersDatabase(self._db_file_name)
        client = self._get_client(connection.name, username, token)
        client.add_connection(connection)
        logging.debug(
            f"CONNECTIONS:Connection {connection.name} "
            f"added to {client.user.username}")
        return connection, client, database_connection

    def _connect_connection(self, connection_advanced_socket):
        """
        Connect a connection
        :param connection_advanced_socket: The advanced socket of the
                                           connection.
        :return: Connection object and its client object and its
                 connection to the database
        """
        connecting_method = connection_advanced_socket.recv(
        ).get_content_as_text()
        logging.info("connecting method: " + connecting_method)
        # TODO: dont decode or use base64 on token
        connection_info = connection_advanced_socket.recv(
        ).get_content_as_text().split("\n")

        try:
            if connecting_method == "login":
                connection, client, db_connection = self._login(
                    connection_advanced_socket,
                    connection_info)
            elif connecting_method == "signup":
                connection, client, db_connection = self._signup(
                    connection_advanced_socket,
                    connection_info)
            elif connecting_method == "token":
                connection, client, db_connection = self._connect_with_token(
                    connection_advanced_socket,
                    connection_info)
            else:
                raise ValueError("Bad method")
        # If an value error occurs, set the connection status to the string of
        # the error
        except ValueError as e:
            error_string = e.args[0]
            if error_string in ("username does not exists",
                                "password is wrong"):
                connection_status = "Username or password are wrong"
            else:
                connection_status = e.args[0]
            connection_advanced_socket.send(Message(
                MESSAGE_TYPES["server interaction"],
                connection_status),
                block_until_buffer_empty=True)
            raise
        else:
            try:
                connection_advanced_socket.send(Message(
                    MESSAGE_TYPES["server interaction"],
                    "ready"))
                # TODO: what if server closes? block=True can hang!
                # Make sure buffers are empty before switching
                client_connection_status = connection_advanced_socket.recv(
                    block=True).get_content_as_text()
                if client_connection_status != "ready":
                    logging.debug(
                        f"CONNECTIONS:Crashed with "
                        f"connection status: {client_connection_status}")
                    raise ValueError(
                        f"Client sent error:{client_connection_status}")
                logging.debug(
                    f"CONNECTIONS:{connection.name} "
                    f"connection status: {client_connection_status}")
            except Exception:
                connection.status = ConnectionStatus.ERROR
                client.remove_connection(connection.name)
                raise
            return connection, client, db_connection

    def _run_main_loop_of_connection(self, connection, client, db_connection):
        """
        Based on the connection type, run its main loop.
        :param connection: The connection object.
        :param client: The client of the connection.
        :param db_connection: The connection to the database of the
                              connection.
        """
        logging.info(
            f"CONNECTIONS:Selecting main loop"
            f"for connection {connection.name}")
        if connection.type == "connector":
            connection.connected = True
            connection.status = ConnectionStatus.CONNECTED
            self._run_connector(connection, client, db_connection)
        elif connection.type == "main":
            connection.connected = True
            connection.status = ConnectionStatus.CONNECTED
            self._run_main(connection, client, db_connection)
        elif connection.type == "settings":
            logging.info("connecting two ways buffered sender socket")
            connection.socket.switch_state(True, True)
            connection.status = ConnectionStatus.CONNECTED
            connection.connected = True
            self._run_buffered_connection_to_partner(connection, client)
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
            connection.status = ConnectionStatus.CONNECTED
            connection.connected = True
            self._run_buffered_connection_to_partner(connection, client)
        elif connection.type in ("keyboard - receiver", "mouse - receiver"):
            logging.info("connecting buffered receiver socket")
            connection.socket.switch_state(True, True)
            # (Does not block) Receivers do not need to send any data.
            # Therefore, the server will never receive from them data
            # and thus, their receiving threads can be closed to conserve
            # CPU usage.
            logging.debug(
                f"closing recv thread of connection {connection.name}")
            connection.socket.close_recv_thread()
            connection.status = ConnectionStatus.CONNECTED
            connection.connected = True
            db_connection.close()
        elif connection.type == "frame - sender":
            logging.info("connecting unbuffered sender socket")
            connection.socket.switch_state(False, True)
            connection.status = ConnectionStatus.CONNECTED
            connection.connected = True
            self._run_connection_to_partner(connection, client)
        elif connection.type == "frame - receiver":
            logging.info("connecting unbuffered receiver socket")
            connection.socket.switch_state(True, False)
            connection.status = ConnectionStatus.CONNECTED
            connection.connected = True
            db_connection.close()
        else:
            raise ValueError("Connection type does not exists")

    @staticmethod
    def _disconnect_partner(connection, client, partner_disconnected):
        """
        # TODO: should this be static or in client?
        Disconnect the partner of the client
        :param connection: The connection of the client
        :param client: the client
        :param partner_disconnected: Whether the partner initiated the
                                    disconnect
        """
        partner = client.partner
        partner_connection = partner.get_connection(connection.name)
        partner_connector = partner.get_connection("connector")

        if not partner_disconnected:
            partner_connector.commands.put(f"close:{connection.name}")
        while True:
            time.sleep(0)  # Release GIL
            if partner_connector.status is not ConnectionStatus.CONNECTED:
                break  # TODO: other side connector crashed
            elif partner_connection.status is not ConnectionStatus.CONNECTED:
                break
        partner.close_connection(partner_connection)

    @staticmethod
    def _disconnect_connection(connection, client, disconnect_error):
        """
        TODO: static or in client.py?
        Disconnect the connection according to the disconnect_error
        :param connection: The connection to disconnect
        :param client: The client of the connection
        :param disconnect_error: The error that caused the disconnect
        """
        # TODO: if isinstance(disconnect_error, ConnectionDisconnectedError):
        # TODO: disconnect partner in another thread?
        if connection.type in ("frame - sender",
                               "keyboard - sender",
                               "mouse - sender",
                               "settings"):
            if not isinstance(disconnect_error,
                              PartnerConnectionDisconnectedError):
                partner_connector = client.partner.get_connection("connector")
                partner_connector.commands.put(f"close:{connection.name}")
                partner_connection = client.partner.get_connection(
                    connection.name)
                # wait for the partner to close and then close
                while True:
                    time.sleep(0)  # Release GIL
                    # TODO: fix the \
                    if partner_connector.status is not \
                            ConnectionStatus.CONNECTED:
                        break  # TODO: other side connector crashed
                    elif partner_connection.status is not \
                            ConnectionStatus.CONNECTED:
                        break
        elif connection.type in ("keyboard - receiver",
                                 "mouse - receiver",
                                 "frame - receiver"):
            Server._disconnect_partner(
                connection,
                client,
                isinstance(disconnect_error,
                           PartnerConnectionDisconnectedError))
        client.close_connection(connection)

    def _run_connection(self, connection_socket, address):
        """
        run a connection to a client until the server closes
        :param connection_socket: the socket of the connection
        :param address: the address of the socket
        """
        connection_advanced_socket = AdvancedSocket()
        connection_advanced_socket.start(connection_socket, True, True)
        try:
            connection, client, db_connection = self._connect_connection(
                connection_advanced_socket)
        # TODO: maybe reconnect socket on value error
        except Exception as e:
            print(e)
            logging.error(f"SERVER:Socket {address} crashed while connecting",
                          exc_info=True)
            try:
                connection_advanced_socket.shutdown()
                connection_advanced_socket.close()
            except Exception as e:
                print(e)
                logging.error(f"SERVER:Crashed while closing {address}",
                              exc_info=True)
        else:
            try:
                self._run_main_loop_of_connection(connection,
                                                  client,
                                                  db_connection)
            except DisconnectedError as disconnect_error:
                Server._disconnect_connection(connection,
                                              client,
                                              disconnect_error)
            except Exception as error:
                logging.error(
                    (f"SERVER:Client {client.user.username}'s connection"
                     f"{connection.name} crashed while running"),
                    exc_info=True)
                try:
                    Server._disconnect_connection(connection,
                                                  client,
                                                  error)
                except Exception as e:
                    print(e)
                    logging.error(("SERVER:Crashed while closing client:"
                                   f"{client.user.username}'s connection:"
                                   f"{connection.name} trying to crash the"
                                   " socket instead"),
                                  exc_info=True)
                    try:
                        if not client.safe_remove_connection(connection):
                            logging.debug(
                                ("SERVER:While crashing connection:"
                                 f"{connection.name} of client: "
                                 f"{client.user.username}, when removing the"
                                 "connection, the client did not have the "
                                 "connection"))
                        connection_advanced_socket.shutdown()
                        connection_advanced_socket.close()
                    except Exception as e:
                        print(e)
                        logging.error(
                            f"SERVER:Crashed while crashing {address}",
                            exc_info=True)

            # If main loop exits and does not raise DisconnectError,
            # then that means it is handled in another thread

    def _accept_connections(self):
        """
        Accept and handle connections until server closes.
        """
        while self.running:
            try:
                connection_socket, address = self._server_socket.accept()
                connection_socket.settimeout(
                    advanced_socket.DEFAULT_REFRESH_RATE)
                secure_connection = context.wrap_socket(
                    connection_socket,
                    server_side=True)
            except ssl.SSLError:
                logging.error("ACCEPT:SSL error:", exc_info=True)
            except socket.timeout:
                pass
            else:
                logging.info(f"ACCEPT:New client: {address}")
                threading.Thread(
                    name=f"Accept {address} thread",
                    target=self._run_connection,
                    args=(secure_connection, address)).start()
        logging.info("ACCEPT:closing server socket")
        try:
            self._server_socket.close()
        except OSError:
            logging.error("ACCEPT:Error while closing server socket",
                          exc_info=True)
        logging.info("ACCEPT:accept thread exiting")

    def start(self,
              address=DEFAULT_SERVER_ADDRESS,
              db_file_name=DEFAULT_DB_FILENAME,
              refresh_rate=DEFAULT_REFRESH_RATE):
        """
        Start the server.
        :param address: The (ip, port) of the server.
        :param db_file_name: The filename of the database.
        :param refresh_rate: The time between checking if threads needs
                             to close.
        """
        self._db_file_name = db_file_name
        self._clients = {}
        # TODO: now need to keep reference since accept thread handles it
        self._server_socket = socket.socket()
        self._server_socket.settimeout(refresh_rate)
        self._server_socket.bind(address)
        self._server_socket.listen()  # TODO: Add parameter here.
        self._accept_connections_thread = threading.Thread(
            name="accept connections thread",
            target=self._accept_connections)
        self._set_running(True)
        self._accept_connections_thread.start()

    def shutdown(self):  # , timeout=None):
        """
        Close all threads
        TODO: remove or keep timeout?
        param timeout: The amount of seconds to wait for threads to
                        close before closing the server
        :raise TimeoutError: If timeout occurs. Some threads might
                             still be open. Call this again to close
                             them. (If no timeout occurs, all threads
                             are closed)
        """
        self._set_running(False)
        if self._accept_connections_thread is not None:
            self._accept_connections_thread.join()
        """timeout_time = None
        current_timeout = timeout
        if timeout is not None:
            timeout_time = time.time() + timeout
        self._set_running(False)
        try:
            if self._accept_connections_thread is not None:
                self._accept_connections_thread.join(current_timeout)
        except RuntimeError as e:
            # Raise if error is not that thread was already closed
            if e.args[0] != 'cannot join thread before it is started':
                raise
        self._accept_connections_thread = None
        if timeout is not None:
            current_timeout = timeout_time - time.time()
            if current_timeout <= 0:
                raise TimeoutError()
        # Other clients can not connect
        with self._clients_threads_lock:
            for client_thread in self._clients_threads.values()[:]:
                if timeout is not None:
                    current_timeout = timeout_time - time.time()
                    if current_timeout <= 0:
                        raise TimeoutError()
                try:
                    client_thread.join(current_timeout)
                except RuntimeError as e:
                    # Raise if error is not that thread was already closed
                    if e.args[0] != 'cannot join thread before it is started':
                        raise
                if not client_thread.is_alive:
                    self._clients_threads.remove(client_thread)"""

    def close(self):
        """
        Close the server.
        """
        # TODO: Make sure all connections are closed before calling close
        #  on server socket
        # with self._clients_lock:
        #    for client in self._clients[:]:
        #        client.close_all_connections()
        self._server_socket.close()
