"""
Manages connections to the server
"""
__author__ = "Ron Remets"

import logging
import threading
import queue

# from communication import communication_protocol
from communication.advanced_socket import (AdvancedSocket,
                                           ConnectionClosed)
from communication.connection import Connection
from communication.message import Message, MESSAGE_TYPES, ENCODING

CONNECTOR_REFRESH_RATE = 1


class ConnectionManager(object):
    """
    Manages connections to the server
    """
    def __init__(self):
        self._running_lock = threading.Lock()
        self._connections_lock = threading.Lock()
        self._tokens_lock = threading.Lock()
        # All the available tokens as dict like {name: token}
        self._tokens = None
        # All the connections
        self._connections = None
        # A queue for connector to know to whom to get tokens
        self._token_requests = None
        # A connection that adds other connections
        self._connector = None
        self._connector_thread = None
        self._server_address = None
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

    @property
    def connections(self):
        """
        :return: A dictionary with all the connections to the server
        """
        with self._connections_lock:
            return self._connections

    def _add_connector(self, username, password, method, callback=None):
        """
        Add a connection that connects other connection to the server
        :param username: The username of the user
        :param password: The password of the user
        :param method: Whether to log in or to sign up
        :param callback: The function to call after connecting
                         (From the connecting thread)
        """
        socket = None
        try:
            socket = AdvancedSocket.create_connected_socket(self._server_address)
            self._connector.socket.start(socket, True, True)
            logging.debug(f"CONNECTION:Sending connector method: {method}")
            self._connector.socket.send(Message(
                MESSAGE_TYPES["server interaction"],
                method))
            logging.debug(f"CONNECTIONS:Sent method")
            logging.debug(f"CONNECTIONS:Sending user info:\n"
                          f"{username}\n"
                          f"{password}\n"
                          f"connector\n"
                          f"connector")
            self._connector.socket.send(Message(
                MESSAGE_TYPES["server interaction"],
                (f"{username}\n"
                 f"{password}\n"
                 f"connector\n"
                 f"connector")))
            logging.debug("CONNECTIONS:Sent user's info")
            logging.debug("CONNECTIONS:Receiving connection status")
            connection_status = self._connector.socket.recv().get_content_as_text()
            logging.info(
                f"CONNECTIONS:Connection status of connector: {connection_status}")
            self._connector.socket.send(Message(
                MESSAGE_TYPES["server interaction"],
                "ready"),
                block_until_buffer_empty=True)
            logging.debug(
                f"CONNECTIONS:connector sent ready")
            # A system admin can send a disconnect request. As a result,
            # we need to make sure connector is ready to receive commands
            # before it is considered connected but because it uses TCP
            # the command must come after 'connected' message and so
            # we dont need to send 'connected' from connector
            self._connector.connected = True
        except ConnectionClosed as e:
            connection_status = "Unexpected close"
            if socket is not None:
                if socket.running:
                    socket.close()
        except Exception as e:
            connection_status = "Exception while creating socket"
        if callback is not None:
            callback(connection_status)

    def _get_token(self, name):
        """
        Request a token for a connection
        :param name: The name of the connection that need the token
        :return: The token as a bytes object
        """
        logging.debug(f"CONNECTIONS:Sending request for token for {name}")
        self._connector.socket.send(Message(
            MESSAGE_TYPES["server interaction"],
            name))
        logging.debug(f"CONNECTIONS:Receiving token for {name}")
        response = self._connector.socket.recv().content.split("\n".encode(
            ENCODING))
        logging.debug(
            f"CONNECTIONS:Received response for token for {name}: {response}")
        return {"status": response[0].decode(), "token": response[1]}

    # TODO: change to just token (get_token_from_connector)
    def _run_connector(self, username, password, method, callback=None):
        """
        Add the connector and run it's main loop until disconnected.
        :param username: The username of the user
        :param password: The password of the user
        :param method: The method to add the connector (see _add_connector)
        :param callback: The function to call after connecting
                         (From the connecting thread)
        """
        self._add_connector(username, password, method, callback=callback)
        while self.running:
            try:
                name = self._token_requests.get(block=True,
                                                timeout=CONNECTOR_REFRESH_RATE)  # TODO: timeout?
            except queue.Empty:  # TODO: any better way to do this?
                pass
            else:
                token = self._get_token(name)  # TODO: what if this crashes?
                with self._tokens_lock:
                    self._tokens[name] = token

    def add_connector(self, username, password, method, callback=None):
        """
        Add the connector connection.
        This is not thread safe.
        You should create connections only from the main thread.
        :param username: The username of the user
        :param password: The password of the user
        :param method: Whether to log in or to sign up
        :param callback: The function to call after connecting
                         (From the connecting thread)
        """
        # This part of add_connector is not thread safe. You should
        # create connections only from the main thread. Because of this,
        # we do not have to maintain lock to self._connector.running
        # between checking if a connection exists and starting it
        if self._connector.running:
            raise ValueError("Connector already exists")
        # Let other threads know this connection is in the middle of
        # connecting
        self._connector.start()
        self._connector_thread = threading.Thread(
            name="Connector connect thread",
            target=self._run_connector,
            args=(username, password, method, callback))
        self._connector_thread.start()

    def _connect_connection(self,
                            connection,
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
        self.connections[connection.name] = connection
        if only_recv:
            connection.socket.close_send_thread()
        if only_send:
            connection.socket.close_recv_thread()
        connection.connected = True
        return connection_status

    def _add_connection(self,
                        username,
                        name,
                        buffer_state,
                        connection_type,
                        callback=None,
                        only_send=False,
                        only_recv=False):
        """
        Add a connection to app. Only call this after sign in or log in.
        :param username: The username of the user
        :param name: The name of the connection
        :param buffer_state: a tuple like
               (input is buffered, output is buffered)
        :param connection_type: The type of connection to report to
               the server
        :param callback: The function to call after connecting
                         (From the connecting thread)
        :param only_send: Whether the connection only needs to send
                          packets
        :param only_recv: Whether the connection only needs to recv
                          packets
        """
        # Request token
        self._token_requests.put(name, block=True)  # TODO: Block? why? how?
        # Wait for connector to get a token
        while True:  # TODO: add timeout or error in response that is timeout
            with self._tokens_lock:
                if name in self._tokens:
                    response = self._tokens.pop(name)  # TODO: error can be client timeout
                    break
        if response["status"] == "ok":
            connection = Connection(name,
                                    AdvancedSocket(),
                                    connection_type)
            # Create and connect a socket. If the an exception is raised
            # while connecting, the socket will close automatically.
            socket = AdvancedSocket.create_connected_socket(
                self._server_address)
            connection.socket.start(socket, True, True)
            connection_status = self._connect_connection(connection,
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
        This part of add_connection is not thread safe.
        You should create connections only from the main thread.
        However, this will put None in
        connection_manager['connection name'] so you can be sure this
        connection is currently connection.
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
        if name in self.connections:
            raise ValueError("Connection already exists")
        # Let other threads know this connection is in the middle of
        # connecting
        self.connections[name] = None
        add_thread = threading.Thread(name=f"Connection {name} connect thread",
                                      target=self._add_connection,
                                      args=(username,
                                            name,
                                            buffer_state,
                                            connection_type,
                                            callback,
                                            only_send,
                                            only_recv))
        add_thread.start()
        if block:
            add_thread.join()  # TODO: remove block as there is not need for it

    def close_connection(self, name, kill=False):  # TODO: kill or block?
        """
        Close a running connection
        :param name: The name of the connection
        :param kill: kill the threads?
        """
        # TODO: maybe on another thread?
        logging.info(f"Closing connection: {name}")
        self.connections[name].close(kill)  # TODO: parameters
        self.connections.pop(name)

    def start(self, server_address):
        """
        Start the connection manager
        :param server_address: The address of the server to whom
                               to connect
        """
        # The server address
        self._server_address = server_address
        # All the connections
        self._connections = dict()
        # all the names of the connections that need tokens
        self._token_requests = queue.SimpleQueue()
        # All the tokens like {connection.name: token}
        self._tokens = {}
        # A connection that adds other connections
        self._connector = Connection("connector",
                                     AdvancedSocket(),
                                     "connector")
        self._set_running(True)

    def close(self, block=True):
        """
        Close the connection manager and all the sockets
        :param block: Whether to wait for all threads to stop.
        """
        # TODO: add kill if block = False
        # TODO: add closing all sockets and threads here
        self._set_running(False)
        if block:
            # TODO: what if not None now but then crash and set to None
            #  => never set this to None
            #  cant use lock cuz of deadlock. its trying to set to none and
            #  join at the same time but the joined thread is locked
            for connection in self.connections.values():
                connection.close()
            if self._connector_thread is not None:
                self._connector_thread.join()
        self._connector.close()
        # TODO: if a socket crashes, it will try to reconnect X times
        #  and then
        #  it will declare server is dead and all sockets will close.
        #  as such we need to be able to reconnect any socket
        #  including connector.
