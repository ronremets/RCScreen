"""
Handles communication between the clients and the server
TODO: Add exception handling.
"""

__author__ = "Ron Remets"

import socket
import threading

import communication_protocol
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

    def _connect_client(self, client_socket):
        """
        Log in or sign up a client.
        :param client_socket: The socket of the client.
        :return: A client.Client object with the client's information.
        """
        message = communication_protocol.recv_packet(client_socket).decode(
            communication_protocol.ENCODING)
        code = message[:message.index("\n")]
        other_code = message[message.index("\n") + 1:]
        client_object = client.Client(client_socket, code, other_code)
        with self._connected_clients_lock:
            self._connected_clients[code] = client_object
        print(client_object)
        connected = False
        while not connected and self.running:
            with self._connected_clients_lock:
                if other_code in self._connected_clients:
                    connected = True
                    client_object.other_client = self._connected_clients[
                        other_code]
        print("done connecting")

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
                    target=self._connect_client,
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
                for code, client_object in self._connected_clients.copy(
                        ).items():
                    if not client_object.running:
                        self._connected_clients.pop(client_object)

    def start(self):
        """
        Start the server.
        """
        self._connected_clients = {}
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
    # TODO: Fix and create a unit test of this.
    """a = Server()
    threads = []
    for i in range(10):
        threads.append(threading.Thread(target=test))
    print("starting")
    a.start()
    for thread in threads:
        thread.start()
    print("started")
    input()
    a.close()
    for thread in threads:
        thread.join()"""
    a = Server()
    a.start()
    try:
        while True:
            pass
    except KeyboardInterrupt:
        pass
    a.close()
