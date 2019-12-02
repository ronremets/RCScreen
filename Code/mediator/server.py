"""
Handles communication between the clients and the server
TODO: Add exception handling.
"""

__author__ = "Ron Remets"

import socket
import threading
import time

some_lock = threading.Lock()
bob = print
def f(*args, **kwargs):
    with some_lock:
        bob(*args, **kwargs)
print = f

import communication_protocol
import client

# TODO: Add a DNS request instead of static IP and port.
SERVER_ADDRESS = ("0.0.0.0", 2125)
TIMEOUT = 2
ENCODING = "ASCII"


class Server(object):
    """
    Handles all communication between clients.
    """
    def __init__(self):
        self._server_socket = None
        self._messages_list = []
        self._connected_clients = []
        self._clients_threads = []
        self._connect_thread = None
        self._remove_closed_threads_thread = None
        self._running_lock = threading.Lock()
        self._connected_clients_lock = threading.Lock()
        self._clients_threads_lock = threading.Lock()
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

    # noinspection PyMethodMayBeStatic
    def _generate_code(self):
        """
        Generate the code for the client
        :return: The code
        """
        with self._connected_clients_lock:
            return str(len(self._connected_clients)).encode(ENCODING)

    def _connect_client(self, client_socket):
        """
        Log in or sign up a client.
        :param client_socket: The socket of the client.
        :return: A client.Client object with the client's information.
        """
        code = self._generate_code()
        communication_protocol.send_message(client_socket,
                                            {"content": b"code: " + code})
        other_code = communication_protocol.recv_packet(client_socket)
        client_object = client.Client(client_socket, code, other_code)
        print(repr(client_object))
        with self._connected_clients_lock:
            self._connected_clients.append(client_object)
        connected = False
        while not connected:
            with self._connected_clients_lock:
                for other_client in self._connected_clients:
                    if other_client.code == other_code:
                        connected = True
                        client_object.other_client = other_client
        print("done")
        return client_object

    def _run_client(self, client_socket):
        """
        Run a client.
        :param client_socket: The client to connect.
        """
        #  TODO: Create a better protocol and maybe store
        #   in communication_protocol
        client_object = self._connect_client(client_socket)
        # print(self._connected_clients)
        # TODO: delete this

    def _add_clients(self):
        """
        Add clients to be connected until server closes.
        """
        while self.running:
            try:
                client_socket, addr = self._server_socket.accept()
                # TODO: Remove and replace with logging.
                print(f"New client: {addr}")
                client_thread = threading.Thread(target=self._run_client,
                                                 args=(client_socket,))
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


def test():
    c = socket.socket()
    c.connect(SERVER_ADDRESS)
    print("connected")
    communication_protocol.send_message(c, {"content": b"2"})
    print("sent")
    print(communication_protocol.recv_packet(c))
    # time.sleep(2)
    c.close()


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
    input()
    a.close()
