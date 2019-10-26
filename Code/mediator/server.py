"""
Handles communication between the clients and the server
"""

__author__ = "Ron Remets"

import time
import socket
import threading

import communication_protocol

SERVER_ADDRESS = ("127.0.0.1", 4567)
TIMEOUT = 2


class Server(object):
    """
    Handles all communication between clients.
    """
    def __init__(self):
        self._server_socket = None
        self._connected_clients = []
        self._clients_threads = []
        self._connect_thread = None
        self._remove_closed_threads_thread = None
        self._running_lock = threading.Lock()
        self._clients_threads_lock = threading.Lock()
        self._set_running(False)

    # noinspection PyMissingOrEmptyDocstring
    @property
    def running(self):
        with self._running_lock:
            return self.__running

    def _set_running(self, value):
        with self._running_lock:
            self.__running = value

    # noinspection PyMethodMayBeStatic
    def _connect_client(self, client):
        """
        Connect a client to another client.
        :param client: The client to connect.
        """
        communication_protocol.send_message(client,
                                            {"content": b"Hello world"})
        print(communication_protocol.recv_packet(client))
        client.close()  # TODO: Remove this.

    def _add_clients(self):
        """
        Add clients to be connected until server closes.
        """
        while self.running:
            try:
                client, addr = self._server_socket.accept()
                print(f"New client: {addr}")
                client_thread = threading.Thread(target=self._connect_client,
                                                 args=(client,))
                with self._clients_threads_lock:
                    self._clients_threads.append(client_thread)
                    client_thread.start()
            except socket.timeout:
                pass

    def _remove_closed_threads(self):
        """
        Remove closed threads from the list of threads until server closes.
        """
        while self.running:
            # Create a shallow copy of the list because of the for loop.
            with self._clients_threads_lock:
                for thread in self._clients_threads[:]:
                    if not thread.is_alive():
                        self._clients_threads.remove(thread)

    def start(self):
        """
        Start the server.
        """
        self._server_socket = socket.socket()
        self._server_socket.settimeout(TIMEOUT)
        self._server_socket.bind(SERVER_ADDRESS)
        self._server_socket.listen()  # TODO: Add parameter here.
        self._connect_thread = threading.Thread(target=self._add_clients)
        self._remove_closed_threads_thread = threading.Thread(
            target=self._remove_closed_threads)
        self._set_running(True)
        self._connect_thread.start()
        self._remove_closed_threads_thread.start()

    def close(self, block=True):
        """
        Close the server.
        :param block: (When True) - Wait for all threads to finish
                      before closing which results in a smoother close.
        """
        self._set_running(False)
        if block:
            self._connect_thread.join()
            self._remove_closed_threads_thread.join()
            for thread in self._clients_threads:
                thread.join()
            self._remove_closed_threads()
        # TODO: Make sure all clients are closed before calling close
        #  on server socket
        self._server_socket.close()


a = Server()
print("starting")
a.start()
print("started")
c = socket.socket()
c.connect(SERVER_ADDRESS)
print("connected")
print(communication_protocol.recv_packet(c))
print("sending")
communication_protocol.send_message(c, {"content": b"Hello world2"})
# time.sleep(5)
a.close()
