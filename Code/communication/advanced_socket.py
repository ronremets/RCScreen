"""
Wrapper for socket for use in the front end.
"""

__author__ = "Ron Remets"

import threading
import socket
import queue

import message_buffer
import communication_protocol

SERVER_ADDRESS = ("127.0.0.1", 2125)
TIMOUT = None


class AdvancedSocket(object):
    """
    Wrapper for socket for use in the front end.
    """
    def __init__(self):
        self._socket = None
        self._buffered = True
        self._recv_thread = None
        self._send_thread = None
        self._messages_received = message_buffer.MessageBuffer(self._buffered)
        self._messages_to_send = message_buffer.MessageBuffer(self._buffered)
        self._messages_received_lock = threading.Lock()
        self._messages_to_send_lock = threading.Lock()
        self._running_lock = threading.Lock()
        self._set_running(False)

    @property
    def running(self):
        with self._running_lock:
            return self.__running

    def _set_running(self, value):
        with self._running_lock:
            self.__running = value

    def _receive_messages(self):
        """
        Receive messages until server closes
        """
        while self.running:
            self._messages_received.add(communication_protocol.recv_packet(
                self._socket))

    def _send_messages(self):
        """
        Send messages until server closes
        """
        while self.running:
            try:
                communication_protocol.send_message(
                    self._socket,
                    self._messages_to_send.pop())
            except queue.Empty:
                pass

    def switch_state(self, input_is_buffered, output_is_buffered):
        """
        Change the state of the socket buffers
        :param input_is_buffered: bool, the input state
        :param output_is_buffered: bool, the output state
        """
        self._messages_received.switch_state(input_is_buffered)
        self._messages_to_send.switch_state(output_is_buffered)

    def send(self, message):
        """
        Send a message.
        :param message: The message to send
        """
        self._messages_to_send.add(message)

    def recv(self):
        """
        Receive a message from the other side
        :return: The message.
        """
        return self._messages_received.pop()

    def start(self, code, other_code, input_is_buffered, output_is_buffered):
        """
        Start the server and its threads.
        """
        self._recv_thread = threading.Thread(target=self._receive_messages)
        self._send_thread = threading.Thread(target=self._send_messages)
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
        self.switch_state(input_is_buffered, output_is_buffered)
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
