"""
Manages connections to the server
"""
__author__ = "Ron Remets"

import logging
import threading
import queue
import time

from communication.advanced_socket import AdvancedSocket
from communication.connection import Connection, ConnectionStatus
from communication.message import Message, MESSAGE_TYPES, ENCODING
from communication.connector import Connector
from communication.client import Client
from communication.user import User


CONNECTOR_REFRESH_RATE = 1


class ConnectionManager(object):
    """
    Manages connections to the server
    """
    def __init__(self):
        self._running_lock = threading.Lock()
        self._tokens_lock = threading.Lock()
        self._client_lock = threading.Lock()
        # All the available tokens as dict like {name: token}
        self._tokens = None
        self._connector_thread = None
        self._server_address = None
        self._set_running(False)
        self._client = None

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

    @property
    def client(self):
        """
        The client that holds all the connections
        :return: A client object. The reference is thread safe but the
                 object itself is not
        """
        with self._client_lock:
            return self._client

    def _add_connector(self, username, password, method, callback=None):
        """
        Add a connection that connects other connection to the server
        :param username: The username of the user
        :param password: The password of the user
        :param method: Whether to log in or to sign up
        :param callback: The function to call after connecting
                         (From the connecting thread)
        """
        connector = self.client.get_connection("connector")
        connection_status = "Unexpected error (unreachable code)"
        try:
            socket = AdvancedSocket.create_connected_socket(
                self._server_address)
            connector.socket.start(socket, True, True)
            logging.debug(f"CONNECTION:Sending connector method: {method}")
            connector.socket.send(Message(
                MESSAGE_TYPES["server interaction"],
                method))
            logging.debug(f"CONNECTIONS:Sent method")
            logging.debug(f"CONNECTIONS:Sending user info:\n"
                          f"{username}\n"
                          f"{password}\n"
                          f"connector\n"
                          f"connector")
            connector.socket.send(Message(
                MESSAGE_TYPES["server interaction"],
                (f"{username}\n"
                 f"{password}\n"
                 f"connector\n"
                 f"connector")))
            logging.debug("CONNECTIONS:Sent user's info")
            logging.debug("CONNECTIONS:Receiving connection status")
            connection_status = connector.socket.recv().get_content_as_text()
            if connection_status != "ready":
                raise ValueError(connection_status)
            logging.info(
                f"CONNECTIONS:Connection status of connector:"
                f" {connection_status}")
            connector.socket.send(Message(
                MESSAGE_TYPES["server interaction"],
                "ready"),
                block_until_buffer_empty=True)
            logging.debug(
                f"CONNECTIONS:connector sent ready")
            connector.status = ConnectionStatus.CONNECTED
        except ValueError as e:
            connector.status = ConnectionStatus.ERROR
            connection_status = str(e)
            # TODO: is that what you want? or should you call a func?
            connector.socket.shutdown()
            connector.socket.close()
            with self._client_lock:
                self._client = None
            raise
        except Exception as e:
            print(e)
            connector.status = ConnectionStatus.ERROR
            connection_status = "Exception while creating socket"
            # TODO: is that what you want? or should you call a func?
            connector.socket.shutdown()
            connector.socket.close()
            with self._client_lock:
                self._client = None
            raise
        finally:
            if callback is not None:
                callback(connection_status)

    def _get_token(self, name):
        """
        Request a token for a connection
        :param name: The name of the connection that need the token
        :return: The token as a bytes object
        """
        connector = self.client.get_connection("connector")
        logging.debug(f"CONNECTIONS:Sending request for token for {name}")
        connector.socket.send(Message(
            MESSAGE_TYPES["server interaction"],
            f"generate token:{name}"))
        logging.debug(f"CONNECTIONS:Receiving token for {name}")
        response = connector.socket.recv().content.split("\n".encode(
            ENCODING))
        logging.debug(
            f"CONNECTIONS:Received response for token for {name}: {response}")
        return {"status": response[0].decode(), "token": response[1]}

    def _generate_token(self, name):
        token = self._get_token(name)  # TODO: what if this crashes?
        with self._tokens_lock:
            self._tokens[name] = token

    def _handle_connector_command(self,
                                  command,
                                  from_queue):
        """
        Execute connector command
        :param command: The command to execute
        :param from_queue: Whether the command came from the connector's
                           queue or from the connector socket
        """
        try:
            instruction, name = Connector.parse_connector_command(command)
        except ValueError:
            logging.error(
                (f"CONNECTOR:client {self.client.usern.username} did not"
                 "provide the required ':' in his connector command"))
            raise ValueError("Missing the name part of the command")
        if instruction == "close":
            self.client.connector_close_connection(name, from_queue)
        elif instruction == "generate token":
            self._generate_token(name)
        elif instruction == "disconnect":
            connector = self.client.get_connection("connector")
            connector.status = ConnectionStatus.DISCONNECTING
        else:
            logging.error(
                (f"CONNECTOR:client {self.client.user.username} sent a"
                 f"command: {command} to connector that does not exist"))
            raise ValueError("Not a command")

    def _run_connector(self, username, password, method, callback=None):
        """
        Add the connector and run it's main loop until disconnected.
        :param username: The username of the user
        :param password: The password of the user
        :param method: The method to add the connector (see _add_connector)
        :param callback: The function to call after connecting
                         (From the connecting thread)
        """
        try:
            self._add_connector(username, password, method, callback=callback)
        except Exception as e:
            print(e)
            return
        connector = self.client.get_connection("connector")
        client_side_is_closing = True
        try:
            while True:
                time.sleep(0)  # Release GIL

                message = connector.socket.recv(block=False)
                if message is not None:
                    command = message.get_content_as_text()
                    self._handle_connector_command(command, False)

                if connector.status is not ConnectionStatus.CONNECTED:
                    client_side_is_closing = True
                    break  # TODO: what to do here?

                time.sleep(0)  # Release GIL
                try:
                    command = connector.commands.get(block=False)
                except queue.Empty:
                    pass
                else:
                    self._handle_connector_command(command, True)

                if connector.status is not ConnectionStatus.CONNECTED:
                    client_side_is_closing = False
                    break  # TODO: what to do here?
        except Exception as e:
            print(e)
            logging.error("CONNECTIONS:Connector error", exc_info=True)
            connector.status = ConnectionStatus.DISCONNECTING
        finally:
            try:
                # TODO: what if this crashes
                self.client.connector_close_all_connections(
                    client_side_is_closing)
            finally:
                with self._client_lock:
                    self._client = None

    def add_connector(self, username, password, method, callback=None):
        """
        Add the connector connection.
        :param username: The username of the user
        :param password: The password of the user
        :param method: Whether to log in or to sign up
        :param callback: The function to call after connecting
                         (From the connecting thread)
        """
        if self.client is not None:
            raise ValueError("Client already exists")

        logging.debug(f"CONNECTIONS:Creating client")
        with self._client_lock:
            self._client = Client(User(username, password))

        self.client.add_connection(Connector("connector",
                                             AdvancedSocket(),
                                             "connector"))

        self._connector_thread = threading.Thread(
            name="Connector connect thread",
            target=self._run_connector,
            args=(username, password, method, callback))
        logging.debug(f"CONNECTIONS:starting connector thread")
        self._connector_thread.start()

    @staticmethod
    def _connect_connection(connection,
                            username,
                            token,
                            buffer_state,
                            only_send=False,
                            only_recv=False):
        """
        Connect a connection to the server
        :param connection: a Connection object ot connect
        :param username: The username of the user
        :param token: The token to use to connect
        :param buffer_state: The buffer's state of the connection
                             (See AdvancedSocket)
        :param only_send: Whether the connection only needs to send
                          packets
        :param only_recv: Whether the connection only needs to recv
                          packets
        :return connection status: A string with the connection status
        """
        logging.debug("CONNECTIONS:Sending method: token")
        connection.socket.send(Message(
            MESSAGE_TYPES["server interaction"],
            "token"))
        logging.debug(f"CONNECTIONS:Sent method")
        logging.debug(f"CONNECTIONS:Sending user info:\n"
                      f"{username}\n"
                      f"{token}\n"
                      f"{connection.type}\n"
                      f"{connection.name}")
        connection.socket.send(Message(
            MESSAGE_TYPES["server interaction"],
            (f"{username}\n"
             f"{token.decode()}\n"  # TODO: you should not have to decode
             f"{connection.type}\n"
             f"{connection.name}")))
        logging.debug(f"CONNECTIONS:Sent user's info")

        # Make sure the server is ready to start the main loop and
        # switch buffers states
        connection_status = connection.socket.recv().get_content_as_text()
        logging.debug(
            f"CONNECTIONS:{connection.name} "
            f"connection status: {connection_status}")
        # Make sure buffers are empty before switching
        connection.socket.send(Message(
            MESSAGE_TYPES["server interaction"],
            "ready"),
            block_until_buffer_empty=True)
        logging.debug(
            f"CONNECTIONS:{connection.name} sent ready")
        connection.socket.switch_state(*buffer_state)
        # TODO: what is this? you added the connection here before!
        connection.status = ConnectionStatus.CONNECTING
        if only_recv:
            connection.socket.close_send_thread()
        if only_send:
            connection.socket.close_recv_thread()
        connection.status = ConnectionStatus.CONNECTED
        return connection_status

    def _add_connection(self,
                        username,
                        name,
                        buffer_state,
                        callback=None,
                        only_send=False,
                        only_recv=False):
        """
        Add a connection to app. Only call this after sign in or log in.
        :param username: The username of the user
        :param name: The name of the connection
        :param buffer_state: a tuple like
               (input is buffered, output is buffered)
        :param callback: The function to call after connecting
                         (From the connecting thread)
        :param only_send: Whether the connection only needs to send
                          packets
        :param only_recv: Whether the connection only needs to recv
                          packets
        """
        # Request token
        connector = self.client.get_connection("connector")
        connection = self.client.get_connection(name)
        # TODO: If connect fail, you need to release the token!
        logging.debug(f"CONNECTIONS:Requesting token for {connection.name}")
        connector.commands.put(f"generate token:{name}")
        # Wait for connector to get a token
        while True:  # TODO: what if connector closes?
            if connector.status is not ConnectionStatus.CONNECTED:
                # TODO: maybe release token here or something
                # TODO: dont you have to return a connection status?
                logging.error(
                    ("CONNECTIONS:connector disconnected aborting token for"
                     f"connection {connection.name}"))
                raise ValueError("Connector disconnected")
            time.sleep(0)
            with self._tokens_lock:
                if name in self._tokens:
                    # TODO: error can be client timeout
                    response = self._tokens.pop(name)
                    break
        if response["status"] == "ok":
            # Create and connect a socket. If the an exception is raised
            # while connecting, the socket will close automatically.
            sock = AdvancedSocket.create_connected_socket(
                self._server_address)
            connection.socket.start(sock, True, True)
            connection_status = ConnectionManager._connect_connection(
                connection,
                username,
                response["token"],
                buffer_state,
                only_send,
                only_recv)
        else:
            # raise ValueError("TOKEN ERROR") TODO: is this what you want?
            connection_status = "TOKEN ERROR"  # TODO: or this?
        if callback is not None:
            callback(connection_status)

    def add_connection(self,
                       username,
                       name,
                       buffer_state,
                       connection_type,
                       block=False,
                       callback=None,
                       only_recv=False,
                       only_send=False):
        """
        Add a connection to app.
        :param username: The username of the user
        :param name: The name of the connection
        :param buffer_state: a tuple like
               (input is buffered, output is buffered)
        :param connection_type: The type of connection to report to
               the server
        :param block: Wait until adding completed
        :param callback: The function to call after connecting
                         (From the connecting thread)
        :param only_send: Whether the connection only needs to send
                          packets
        :param only_recv: Whether the connection only needs to recv
                          packets
        """
        logging.info(f"CONNECTIONS:Adding connection '{name}'")
        # This part of add_connection is not thread safe. You should
        # create connections only from the main thread. Because of this,
        # we do not have to maintain lock to self.connection between
        # checking if a connection exists and setting it to None
        if self.client.has_connection(name):
            raise ValueError("Connection already exists")
        # Let other threads know this connection is in the middle of
        # connecting
        self.client.add_connection(Connection(name,
                                              AdvancedSocket(),
                                              connection_type))
        add_thread = threading.Thread(name=f"Connection {name} connect thread",
                                      target=self._add_connection,
                                      args=(username,
                                            name,
                                            buffer_state,
                                            callback,
                                            only_send,
                                            only_recv))
        add_thread.start()
        if block:
            add_thread.join()  # TODO: remove block as there is not need for it

    def close_connection(self, name):
        """
        Close a running connection
        :param name: The name of connection to close
        """
        connector = self.client.get_connection("connector")
        connector.commands.put(f"close:{name}")
        connection = self.client.get_connection(name)
        self.client.close_connection(connection)

    def start(self, server_address):
        """
        Start the connection manager
        :param server_address: The address of the server to whom
                               to connect
        """
        # The server address
        self._server_address = server_address
        # All the tokens like {connection.name: token}
        self._tokens = {}
        self._set_running(True)

    def close(self):  # , block=True):
        """
        Close the connection manager and all the sockets
        param block: Whether to wait for all threads to stop.
        """
        # connections = list(self.connections.values())
        # for connection in connections[:]:
        #     self.close_connection(connection.name)
        self._set_running(False)
        # self._connector.close()
        try:
            if self.client is not None:
                self.client.get_connection("connector").commands.put(
                    "disconnect:")
                for connection in self.client.get_all_connections():
                    self.close_connection(connection.name)
        except Exception as e:
            print(e)
            logging.error("CONNECTIONS:Cant close connections")
        """"# TODO: add kill if block = False
        # TODO: add closing all sockets and threads here
        self._set_running(False)
        if block:
            # TODO: what if not None now but then crash and set to None
            #  => never set this to None
            #  cant use lock cuz of deadlock. its trying to set to none and
            #  join at the same time but the joined thread is locked
            for connection in self.connections.values():
                connection.close()
            try:
                self._connector_thread.join()
            except AttributeError:
                pass  # Thread not created
            except RuntimeError:
                pass  # Thread not started or closed
        self._connector.close()
        # TODO: if a socket crashes, it will try to reconnect X times
        #  and then
        #  it will declare server is dead and all sockets will close.
        #  as such we need to be able to reconnect any socket
        #  including connector."""
