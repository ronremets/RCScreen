"""
Wrapper for socket for sending messages.
"""
__author__ = "Ron Remets"

import logging
import queue
from socket import timeout as socket_timeout
from socket import socket as socket_object
import threading
import time

import lz4.frame

from communication.message import (Message,
                                   MESSAGE_LENGTH_LENGTH,
                                   MESSAGE_TYPE_LENGTH,
                                   ENCODING)
from communication import message_buffer

# The time in seconds that the sockets have to receive or send before
# they check if they have to close.
DEFAULT_REFRESH_RATE = 1
# The buffer size used when receiving.
DEFAULT_LENGTH_BUFFER_SIZE = 2**4
DEFAULT_TYPE_BUFFER_SIZE = 2**2
DEFAULT_CONTENT_BUFFER_SIZE = 2**16


class ConnectionClosed(ConnectionError):
    """
    Raised when a connection is closed while reading or writing to it
    """
    pass


class AdvancedSocket(object):
    """
    Wrapper for socket for sending messages.
    """
    def __init__(self):
        self._socket = None
        self._send_thread = None
        self._recv_thread = None
        self._messages_to_send = message_buffer.MessageBuffer()
        self._messages_received = message_buffer.MessageBuffer()
        self._is_sending = False
        self._is_receiving = False
        self._is_sending_lock = threading.Lock()
        self._is_receiving_lock = threading.Lock()
        self._send_error_state_lock = threading.Lock()
        self._recv_error_state_lock = threading.Lock()
        self._send_error_state = None
        self._recv_error_state = None

    @property
    def running(self):
        """
        Whether the socket is running
        :return: A bool
        """
        with self._is_sending_lock:
            with self._is_receiving_lock:
                return self._is_sending or self._is_receiving

    @property
    def send_error_state(self):
        """
        If the thread that sends messages had an exception, it will go
        here.
        :return: None if send thread does not have an exception,
                 otherwise the exception object.
        """
        with self._send_error_state_lock:
            return self.send_error_state

    @property
    def recv_error_state(self):
        """
        If the thread that receives messages had an exception, it will
        go here.
        :return: None if recv thread does not have an exception,
                 otherwise the exception object.
        """
        with self._recv_error_state_lock:
            return self.recv_error_state

    @staticmethod
    def _pack_message(message):
        """
        Pack a message object to bytes.
        :return: The message in bytes.
        """
        packed_content = lz4.frame.compress(message.content)
        packet_header = (
            str(len(packed_content)).zfill(MESSAGE_LENGTH_LENGTH)
            + str(message.message_type).zfill(MESSAGE_TYPE_LENGTH))
        packet = packet_header.encode(ENCODING) + packed_content
        return packet

    @staticmethod
    def create_connected_socket(address):
        """
        Create and connect a socket. Used in cases where there is no
        socket to wrap AdvancedSocket around and instead one has to be
        created.

        If an exception is raised, the socket object is closed.
        :param address: The address to connect to like (ip, port)
        :return: A socket object
        """
        socket = socket_object()
        try:
            socket.connect(address)
        except Exception:
            socket.close()
            raise
        return socket

    def _send_raw_data(self, data):
        """
        Send a data with a socket.
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
            except socket_timeout:  # Raised by the socket after timeout
                pass
            finally:
                with self._is_sending_lock:
                    if not self._is_sending:
                        raise ConnectionClosed()

    def _recv_fixed_length_data(self, length, buffer_size):
        """
        Receives a fixed length packet from the socket.
        :param length: The length of the packet.
        :param buffer_size: The size of the buffer used by th recv
        :return: The length of the packet
        :raise RuntimeError: If socket is closed from the other side.
        :raise ConnectionClosed: If connection was closed while sending
        """
        data = bytearray(length)
        bytes_received = 0
        while bytes_received < length:
            try:
                data_chunk = self._socket.recv(
                    min(length - bytes_received, buffer_size))
                chunk_length = len(data_chunk)
                if data_chunk == b"":
                    raise RuntimeError("socket connection broken")
                data[bytes_received:bytes_received + chunk_length] = data_chunk
                bytes_received += chunk_length
            except socket_timeout:  # Raised by the socket after timeout
                pass
            finally:
                with self._is_receiving_lock:
                    if not self._is_receiving:
                        raise ConnectionClosed()
        return data

    def _recv_message(self, buffer_size):
        """
        Receive a message from a socket.
        :param buffer_size: The size of the buffer used by th recv
        :return: The packet as a message object
        :raise RuntimeError: If socket is closed from the other side.
        :raise ConnectionClosed: If connection was closed while sending
        """
        length = int(self._recv_fixed_length_data(
            MESSAGE_LENGTH_LENGTH,
            DEFAULT_LENGTH_BUFFER_SIZE).decode(ENCODING))
        message_type = self._recv_fixed_length_data(
            MESSAGE_TYPE_LENGTH,
            DEFAULT_TYPE_BUFFER_SIZE).decode(ENCODING)
        content = lz4.frame.decompress(self._recv_fixed_length_data(
            length,
            buffer_size))
        return Message(message_type, content)

    def _send_messages(self):
        """
        Send messages until server closes
        """
        try:
            while True:
                # Check that you do not have to close the connection.
                # If you do, raise an exception to close the thread.
                with self._is_sending_lock:
                    if not self._is_sending:
                        raise ConnectionClosed()
                # Check if a message is available
                message = self._messages_to_send.pop()
                time.sleep(0)
                # If it is not, try again
                if message is None:
                    continue
                logging.debug("advanced_socket:Sending message: %s",
                              repr(message))
                self._send_raw_data(
                    AdvancedSocket._pack_message(message))
        except ConnectionClosed:
            logging.debug("advanced_socket:Socket send thread closed normally")
        except Exception as e:
            logging.error(
                "advanced_socket:Socket send thread crashed with error:",
                exc_info=True)
            # Update the error state of this thread
            with self._send_error_state_lock:
                self._send_error_state = e
        finally:
            logging.info("advanced_socket:Closed send thread of socket")

    def _receive_messages(self, buffer_size):
        """
        Receive messages until server closes
        :param buffer_size: The size of the buffer used by th recv
        """
        message = None
        try:
            while True:
                # Check that you do not have to close the connection.
                # If you do, raise an exception to close the thread.
                with self._is_receiving_lock:
                    if not self._is_receiving:
                        raise ConnectionClosed()
                # If you do not have a message you have to add to
                # self._messages_received, you can receive another
                # message
                if message is None:
                    message = self._recv_message(buffer_size)
                    logging.debug("advanced_socket:Received message: %s",
                                  repr(message))
                # Attempt to add a message
                try:
                    self._messages_received.add(message)
                except queue.Full:
                    # Can not add a message right now, queue is full.
                    pass
                else:
                    message = None
        except ConnectionClosed:
            logging.debug("advanced_socket:Socket recv thread closed normally")
        except Exception as e:
            logging.error(
                "advanced_socket:Socket recv thread crashed with error:",
                exc_info=True)
            # Update the error state of this thread
            with self._recv_error_state_lock:
                self._recv_error_state = e
        finally:
            logging.warning("advanced_socket:Closed recv thread of socket")

    def close_send_thread(self):
        """
        Close the sending thread so that the socket can only recv
        data. Use this to reduce the amount of threads the sockets uses.
        """
        with self._is_sending_lock:
            self._is_sending = False

    def close_recv_thread(self):
        """
        Close the receiving thread so that the socket can only send
        data. Use this to reduce the amount of threads the sockets uses.
        """
        with self._is_receiving_lock:
            self._is_receiving = False

    def send(self, message, block_until_buffer_empty=False):
        """
        Send a message.
        :param message: The message to send.
        :param block_until_buffer_empty: Block until the message buffer
                                         is empty. This means that all
                                         the messages that were supposed
                                         to be sent were sent or about
                                         to be sent and the buffer can
                                         safely switch state.
        :raise ConnectionClosed: If the connection (or just the send
                                 thread) were closed while or before
                                 sending.
        """
        with self._is_sending_lock:
            if not self._is_sending:
                raise ConnectionClosed()
        with self._send_error_state_lock:
            if self._send_error_state is not None:
                raise self._send_error_state
        self._messages_to_send.add(message)
        if block_until_buffer_empty:
            while not self._messages_to_send.empty():
                with self._is_sending_lock:
                    if not self._is_sending:
                        raise ConnectionClosed()
                with self._send_error_state_lock:
                    if self._send_error_state is not None:
                        raise self._send_error_state

    def recv(self, block=True):
        """
        Receive a message from the other side.
        :param block: Block until recv successful.
        :return: The message.
        :raise ConnectionClosed: If the connection (or just the recv
                                 thread) were closed while or before
                                 receiving.
        """
        with self._is_receiving_lock:
            if not self._is_receiving:
                raise ConnectionClosed()
        with self._recv_error_state_lock:
            if self._recv_error_state is not None:
                raise self._recv_error_state
        message_received = self._messages_received.pop()
        while block and message_received is None:
            message_received = self._messages_received.pop()
            with self._is_receiving_lock:
                if not self._is_receiving:
                    raise ConnectionClosed()
            with self._recv_error_state_lock:
                if self._recv_error_state is not None:
                    raise self._recv_error_state
        return message_received

    def switch_state(self, input_is_buffered, output_is_buffered):
        """
        Change the state of the socket buffers
        :param input_is_buffered: bool, the input state
        :param output_is_buffered: bool, the output state
        """
        self._messages_received.switch_state(input_is_buffered)
        self._messages_to_send.switch_state(output_is_buffered)

    def start(self,
              socket,
              input_is_buffered,
              output_is_buffered,
              refresh_rate=DEFAULT_REFRESH_RATE,
              buffer_size=DEFAULT_CONTENT_BUFFER_SIZE):
        """
        Start sending and receiving messages.
        :param socket: The socket to use to send.
        :param input_is_buffered: Whether the messages received should
                                  be buffered.
        :param output_is_buffered: Whether the messages sent should be
                                  buffered.
        :param refresh_rate: The time between checks of whether the
                             the socket or parts of it need to close.
        :param buffer_size: The size of the recv buffer.
        """
        self._socket = socket
        self._socket.settimeout(refresh_rate)
        self._send_thread = threading.Thread(
            name="AdvancedSocket send thread",
            target=self._send_messages)
        self._recv_thread = threading.Thread(
            name="AdvancedSocket recv thread",
            target=self._receive_messages,
            args=(buffer_size,))
        self.switch_state(input_is_buffered, output_is_buffered)
        self._is_sending = True
        self._is_receiving = True
        self._send_thread.start()
        self._recv_thread.start()

    def shutdown(self, block=True):
        """
        Shutdown the socket threads.
        Use this before close.
        :param block: Block until threads are closed
        """
        logging.debug("advanced_socket:Shutting down sockets threads")
        self.close_send_thread()
        self.close_recv_thread()
        if block:
            try:
                self._recv_thread.join()
            except AttributeError:
                pass  # Thread not created
            except RuntimeError:
                pass  # Thread not started or closed
            try:
                self._send_thread.join()
            except AttributeError:
                pass  # Thread not created
            except RuntimeError:
                pass  # Thread not started or closed

    def close(self):
        """
        Close the socket.
        Shutdown the socket before this to prevent crashing.
        """
        logging.debug("advanced_socket:Closing socket")
        try:
            self._socket.close()
        except AttributeError:
            pass  # Socket not started
        self._socket = None
        logging.debug("advanced_socket:Closed socket")
