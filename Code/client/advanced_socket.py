"""
Wrapper for socket for use in the front end.
"""

__author__ = "Ron Remets"

import threading
import socket
# import queue

import communication_protocol

SERVER_ADDRESS = ("127.0.0.1", 2125)
TIMOUT = None


class AdvancedSocket(object):
    """
    Wrapper for socket for use in the front end.
    """
    def __init__(self):
        self._socket = None
        # self._recv_packet_queue = None
        # self._packet_to_send_queue = None
        self._recv_thread = None
        self._send_thread = None
        self._data_received_lock = threading.Lock()
        self._data_to_send_lock = threading.Lock()
        self._running_lock = threading.Lock()
        self._set_running(False)
        self.data_received = None
        self.data_to_send = None

    @property
    def running(self):
        with self._running_lock:
            return self.__running

    def _set_running(self, value):
        with self._running_lock:
            self.__running = value

    @property
    def data_to_send(self):
        with self._data_to_send_lock:
            return self.__data_to_send

    @data_to_send.setter
    def data_to_send(self, value):
        with self._data_to_send_lock:
            self.__data_to_send = value

    @property
    def data_received(self):
        with self._data_received_lock:
            return self.__data_received

    @data_received.setter
    def data_received(self, value):
        with self._data_received_lock:
            self.__data_received = value

    def _recv_packets(self):
        while self.running:
            # try:
            #    self._recv_packet_queue.put(
            #        communication_protocol.recv_packet(self._socket))
            # except queue.Full:
            #    pass
            self.data_received = communication_protocol.recv_packet(
                self._socket)

    def _send_messages(self):
        while self.running:
            # try:
            #    communication_protocol.send_message(
            #        self._socket,
            #        self._packet_to_send_queue.get())
            # except queue.Empty:
            #    pass
            data_to_send = self.data_to_send
            if data_to_send is not None:
                communication_protocol.send_message(
                    self._socket,
                    data_to_send)

    def start(self, code, other_code):
        """
        Start the server and its threads.
        """
        self._recv_thread = threading.Thread(target=self._recv_packets)
        self._send_thread = threading.Thread(target=self._send_messages)
        # self._packet_to_send_queue = queue.SimpleQueue()
        # self._recv_packet_queue = queue.SimpleQueue()
        self._socket = socket.socket()
        self._socket.settimeout(TIMOUT)
        self._socket.connect(SERVER_ADDRESS)
        communication_protocol.send_message(
            self._socket,
            {"content": f"{code}\n{other_code}".encode(
                communication_protocol.ENCODING)})
        # This suck change this
        # is bad dont it you have so much to live for
        # injection is inevitable (sql injection)
        self._set_running(True)
        self._send_thread.start()
        self._recv_thread.start()

    def close(self, kill=False):
        """
        Close the threads and socket
        :param kill: kill the threads
        """
        self._set_running(False)
        if not kill:
            self._recv_thread.join()
            self._send_thread.join()
        self._socket.close()
