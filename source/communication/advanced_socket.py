"""
Wrapper for socket for sending messages.
"""
__author__ = "Ron Remets"

import logging
import socket
import threading

import lz4.frame

from message import (Message,
                     MESSAGE_LENGTH_LENGTH,
                     MESSAGE_TYPE_LENGTH,
                     ENCODING)
import message_buffer

TIMEOUT = None
BUFFER_SIZE = 1024  # The buffer size used when receiving and sending
FRAG_SUFFIX = "FRAG".encode(ENCODING)
END_FRAG_SUFFIX = "DONE".encode(ENCODING)


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
        self._close_connection = False
        self._running_lock = threading.Lock()
        self._close_connection_lock = threading.Lock()
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

    @staticmethod
    def _pack_message(message):
        """
        Pack a message object to bytes.
        :return: The message in bytes.
        """
        logging.debug(
            f"COMM PROTOCOL:OUT CONTENT: {len(message.content)} bytes")
        packed_content = lz4.frame.compress(message.content)
        packet_header = (
            str(len(packed_content)).zfill(MESSAGE_LENGTH_LENGTH)
            + str(message.message_type).zfill(MESSAGE_TYPE_LENGTH))
        packet = packet_header.encode(ENCODING) + packed_content
        return packet

    def _recv_fixed_length_data(self, length):
        """
        Receives a fixed length packet from the socket.
        :param length: The length of the packet.
        :return: The length of the packet
        :raise RuntimeError: If socket is closed from the other side.
        :raise ConnectionClosed: If connection was closed while sending
        """
        data = bytearray(length)
        bytes_received = 0
        while bytes_received < length:
            try:
                data_chunk = self._socket.recv(
                    min(length - bytes_received, BUFFER_SIZE))
                chunk_length = len(data_chunk)
                if data_chunk == b"":
                    raise RuntimeError("socket connection broken")
                data[bytes_received:bytes_received + chunk_length] = data_chunk
                bytes_received += chunk_length
            except BlockingIOError:
                pass  # Raised since no data was available
            finally:
                with self._close_connection_lock:
                    if self._close_connection:
                        raise ConnectionClosed()
        return data

    def _recv_message(self):
        """
        Receive a message from a socket.
        :return: The packet as a message object
        :raise RuntimeError: If socket is closed from the other side.
        :raise ConnectionClosed: If connection was closed while sending
        """
        length = int(self._recv_fixed_length_data(MESSAGE_LENGTH_LENGTH))
        message_type = self._recv_fixed_length_data(MESSAGE_TYPE_LENGTH)
        content = lz4.frame.decompress(self._recv_fixed_length_data(length))
        try:
            if length < 1000:
                logging.debug(
                    f"COMM PROTOCOL:IN CONTENT: {content.decode(ENCODING)}")
            else:
                logging.debug(
                    f"COMM PROTOCOL:IN CONTENT: {len(content)} bytes")
        except UnicodeError:
            logging.debug(
                f"COMM PROTOCOL:IN CONTENT: bad {len(content)} bytes")
        return Message(message_type, content)

    def _send_raw_data(self, data):
        """
        Send a data with a socket..
        :param data: The data to send
        :raise RuntimeError: If socket is closed from the other side.
        :raise ConnectionClosed: If connection was closed while sending
        """
        total_bytes_sent = 0
        while total_bytes_sent < len(data):
            try:
                bytes_sent = self._socket.send(data[total_bytes_sent:])
                if bytes_sent == 0:
                    raise RuntimeError("socket connection broken")
                total_bytes_sent += bytes_sent
            except BlockingIOError:
                pass  # Raised since no data was available
            finally:
                with self._close_connection_lock:
                    if self._close_connection:
                        raise ConnectionClosed()

    def _receive_messages(self):
        """
        Receive messages until server closes
        """
        try:
            while self.running:
                self._messages_received.add(self._recv_message())
        except ConnectionClosed:
            pass

    def _send_messages(self):
        """
        Send messages until server closes
        """
        try:
            while self.running:
                message = self._messages_to_send.pop()
                if message is not None:
                    self._send_raw_data(AdvancedSocket._pack_message(message))
        except ConnectionClosed:
            pass

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
        self._socket.setblocking(False)
        self._recv_thread = threading.Thread(
            name="AdvancedSocket recv thread",
            target=self._receive_messages)
        self._send_thread = threading.Thread(
            name="AdvancedSocket send thread",
            target=self._send_messages)
        self.switch_state(input_is_buffered, output_is_buffered)
        self._close_connection = False
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
        with self._close_connection_lock:
            self._close_connection = True
        if not kill:
            self._recv_thread.join()
            self._send_thread.join()
        self._socket.close()
