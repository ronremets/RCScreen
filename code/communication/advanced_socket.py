"""
Wrapper for socket for sending messages.
"""
__author__ = "Ron Remets"

import logging
import socket
import threading

import communication_protocol
import message_buffer

TIMEOUT = None


class ConnectionClosed(ConnectionError):
    """
    Raised when a connection is closed while reading or writing to it
    """
    pass


class AdvancedSocket(object):
    """
    Wrapper for socket for sending messages.
    """
    def __init__(self, address=None, timeout=TIMEOUT):
        self._address = address
        self._socket = None
        self._recv_thread = None
        self._send_thread = None
        self._timeout = timeout
        self._messages_received = message_buffer.MessageBuffer()
        self._messages_to_send = message_buffer.MessageBuffer()
        self._running_lock = threading.Lock()
        self._set_running(False)

    @property
    def running(self):
        """
        Whether the socket is running
        :return: A bool
        """
        with self._running_lock:
            return self._running

    def _set_running(self, value):
        with self._running_lock:
            self._running = value

    def _receive_messages(self):
        """
        Receive messages until server closes
        """
        while self.running:
            try:
                self._messages_received.add(
                    communication_protocol.recv_message(self._socket))
            except socket.timeout:
                logging.error("Socket timed out", exc_info=True)
                self.close(kill=True)

    def _send_messages(self):
        """
        Send messages until server closes
        """
        while self.running:
            message = self._messages_to_send.pop()
            if message is not None:
                try:
                    communication_protocol.send_message(
                        self._socket,
                        message,
                        self._timeout)
                except socket.timeout:
                    logging.error("Socket timed out", exc_info=True)
                    self.close(kill=True)

    def switch_state(self, input_is_buffered, output_is_buffered):
        """
        Change the state of the socket buffers
        :param input_is_buffered: bool, the input state
        :param output_is_buffered: bool, the output state
        """
        self._messages_received.switch_state(input_is_buffered)
        self._messages_to_send.switch_state(output_is_buffered)

    def send(self, message, block_until_buffer_empty=False):
        """
        Send a message.
        :param message: The message to send
        :param block_until_buffer_empty: Block until the message buffer
                                         is empty. This means that all
                                         the messages that were supposed
                                         to be sent were sent or about
                                         it be sent and the buffer can
                                         safely switch state.
        """
        self._messages_to_send.add(message)
        if block_until_buffer_empty:
            while self.running and not self._messages_to_send.empty():
                pass
            if not self.running:
                raise ConnectionClosed()

    def recv(self, block=True):
        """
        Receive a message from the other side
        :param block: Block until recv successful
        :return: The message.
        """
        message_received = self._messages_received.pop()
        while self.running and block and message_received is None:
            message_received = self._messages_received.pop()
        if not self.running:
            raise ConnectionClosed()
        return message_received

    def start(self, input_is_buffered, output_is_buffered, client_socket=None):
        """
        Start the server and its threads.
        """
        if client_socket is None:
            self._socket = socket.socket()
            self._socket.connect(self._address)
        else:
            self._socket = client_socket
        self._recv_thread = threading.Thread(target=self._receive_messages)
        self._send_thread = threading.Thread(target=self._send_messages)
        self.switch_state(input_is_buffered, output_is_buffered)
        self._set_running(True)
        self._send_thread.start()
        self._recv_thread.start()

    def close(self, kill=False):
        """
        Close the threads and socket
        :param kill: kill the threads
        """
        logging.info("CONNECTIONS:Closing socket")
        self._set_running(False)
        if not kill:
            self._recv_thread.join()
            self._send_thread.join()
        self._socket.close()
