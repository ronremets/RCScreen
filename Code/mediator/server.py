"""
Handles communication between the clients and the server
TODO: Add exception handling.
"""

__author__ = "Ron Remets"

import socket
import threading

from data.user import User
from communication.message import Message, MESSAGE_TYPES
from communication import communication_protocol
from communication.advanced_socket import AdvancedSocket
import client

# TODO: Add a DNS request instead of static IP and port.
SERVER_ADDRESS = ("0.0.0.0", 2125)
TIMEOUT = 2


class Server(object):
    """
    Handles all communication between clients.
    """
    def __init__(self):
        self._server_socket = None
        self._connected_clients = None
        self._connect_clients_thread = None
        self._remove_closed_clients_thread = None
        self._running_lock = threading.Lock()
        self._connected_clients_lock = threading.Lock()
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

    def _run_connection(self, client_socket):
        """
        run a connection to a client until the server closes
        :param client_socket: the socket of the connection
        """
        client_object, socket_type = self._connect_socket(client_socket)
        # TODO: fix: getpeerbyname might not be supported on all systems
        connection = AdvancedSocket(client_socket.getpeerbyname())
        if socket_type == "main":
            connection.start(True, True, client_socket)
        elif socket_type in ("frame", "sound", "mouse move"):
            other_username = communication_protocol.recv_message(client_socket)
            other_client = None
            found_username = False
            while not found_username:
                with self._connected_clients_lock:
                    for current_client in self._connected_clients:
                        if other_username == current_client.user.username:
                            other_client = current_client
                            found_username = True
            connection.start(False, True, client_socket)
        elif socket_type in ("keyboard", "mouse button"):
            connection.start(True, False, client_socket)
        while client_object.running:
            if socket_type == "main":
                pass
            if socket_type == "frame":
                other_client.send(client_object.recv())
        client_object.close()

    def _connect_socket(self, client_socket):
        """
        connect a socket to a client
        :param client_socket: The socket of the client.
        :return: The client object of the socket
        """
        client_info = communication_protocol.recv_message(
            client_socket).content.decode(communication_protocol.ENCODING)
        client_info = client_info.split("\n")
        username = client_info[0]
        password = client_info[1]
        # TODO: add something like logging in here
        user = User(username, password)
        socket_type = client_info[2]
        client_is_new = True
        client_object = None
        with self._connected_clients_lock:
            for current_client in self._connected_clients:
                if user == current_client.user:
                    current_client.add_socket(client_socket, socket_type)
                    client_is_new = False
                    client_object = current_client
                    break
            if client_is_new:
                client_object = client.Client(user)
                client_object.add_socket(client_socket, socket_type)
                self._connected_clients.append(client_object)
        communication_protocol.send_message(client_socket, Message(
            MESSAGE_TYPES["server interaction"],
            "Connected".encode(communication_protocol.ENCODING)))
        print("done connecting")
        return client_object, socket_type

    def _add_clients(self):
        """
        Add clients to be connected until server closes.
        """
        while self.running:
            try:
                client_socket, addr = self._server_socket.accept()
                # TODO: Remove and replace with logging.
                print(f"New client: {addr}")
                threading.Thread(
                    target=self._run_connection,
                    args=(client_socket,)).start()
            except socket.timeout:
                pass

    def _remove_closed_clients(self):
        """
        Remove closed clients from the list of clients until server
         closes.
        """
        while self.running:
            with self._connected_clients_lock:
                # Create a shallow copy of the list because of the
                # for loop.
                for client_object in self._connected_clients[:]:
                    if not client_object.running:
                        self._connected_clients.remove(client_object)

    def start(self):
        """
        Start the server.
        """
        # maybe use a dict like {user:client}
        self._connected_clients = []
        self._server_socket = socket.socket()
        self._server_socket.settimeout(TIMEOUT)
        self._server_socket.bind(SERVER_ADDRESS)
        self._server_socket.listen()  # TODO: Add parameter here.
        self._connect_clients_thread = threading.Thread(
            target=self._add_clients)
        self._remove_closed_clients_thread = threading.Thread(
            target=self._remove_closed_clients)
        self._set_running(True)
        self._connect_clients_thread.start()
        self._remove_closed_clients_thread.start()

    def close(self, block=True):
        """
        Close the server.
        :param block: (When True) - Wait for all threads to finish
                      before closing which results in a smoother close.
        """
        self._set_running(False)
        if block:
            self._connect_clients_thread.join()
            self._remove_closed_clients_thread.join()
        # TODO: Make sure all clients are closed before calling close
        #  on server socket
        self._server_socket.close()


if __name__ == "__main__":
    a = Server()
    a.start()
    input()
    a.close()
