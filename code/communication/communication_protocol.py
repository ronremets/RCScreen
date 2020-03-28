"""
The protocol used for the socket communication.
"""
__author__ = "Ron Remets"

import time
import logging

import lz4.frame

from message import Message,  MESSAGE_LENGTH_LENGTH, MESSAGE_TYPE_LENGTH

BUFFER_SIZE = 1024  # The buffer size used when receiving and sending.
ENCODING = "ASCII"  # The encoding used in the protocol.
FRAG_SUFFIX = "FRAG".encode(ENCODING)
END_FRAG_SUFFIX = "DONE".encode(ENCODING)


def _pack_message(message):
    """
    Pack a message object to bytes.
    :return: The message in bytes.
    """
    logging.debug(f"COMM PROTOCOL:OUT CONTENT: {len(message.content)} bytes")
    packed_content = lz4.frame.compress(message.content)
    length = len(packed_content)
    packet = (
            str(length).zfill(MESSAGE_LENGTH_LENGTH).encode(ENCODING)
            + str(message.message_type).zfill(
                MESSAGE_TYPE_LENGTH).encode(ENCODING)
            + packed_content)
    return packet


def _recv_fixed_length_data(socket, length, timeout=None, start_time=0.0):
    """
    Receives a fixed length packet from a socket.
    :param socket: The socket to receive with.
    :param length: The length of the packet.
    :param timeout: If not set to None, the timeout in seconds
                    (not accurate use with caution)
    :param start_time: The time since the start of the operation
    :return: The length of the packet
    :raise RuntimeError: If socket is closed from the other side.
    :raise TimeoutError: If timeout was not None and operation timed out
    """
    data = bytearray()
    bytes_received = 0
    while bytes_received < length:
        if timeout is not None:
            socket.settimeout(timeout - (time.time() - start_time))
        data_chunk = socket.recv(min(length - bytes_received, BUFFER_SIZE))
        if data_chunk == b"":
            raise RuntimeError("socket connection broken")
        data.extend(data_chunk)
        bytes_received += len(data_chunk)
    return data


def recv_message(socket, timeout=None):
    """
    Receive a packet from a socket.
    :param socket: The socket to receive with.
    :param timeout: If not set to None, the timeout in seconds
                    (not accurate use with caution)
    :return: The packet in bytes
    :raise RuntimeError: If socket is closed from the other side.
    """
    start_time = 0.0
    if timeout is not None:
        start_time = time.time()
    else:
        socket.settimeout(None)
    length = int(_recv_fixed_length_data(socket,
                                         MESSAGE_LENGTH_LENGTH,
                                         timeout,
                                         start_time))
    message_type = _recv_fixed_length_data(socket,
                                           MESSAGE_TYPE_LENGTH,
                                           timeout,
                                           start_time)
    content = lz4.frame.decompress(_recv_fixed_length_data(socket,
                                                           length,
                                                           timeout,
                                                           start_time))
    try:
        if length < 1000:
            logging.debug(
                f"COMM PROTOCOL:IN CONTENT: {content.decode(ENCODING)}")
        else:
            logging.debug(f"COMM PROTOCOL:IN CONTENT: {len(content)} bytes")
    except UnicodeError:
        logging.debug(f"COMM PROTOCOL:IN CONTENT: bad {len(content)} bytes")
    return Message(message_type, content)


def _send_raw_data(socket, data):  # TODO: delete this
    """
    Send a data with a socket.
    :param socket: The socket to send with.
    :param data: The data to send
    :raise RuntimeError: If socket is closed from the other side.
    """
    total_bytes_sent = 0
    while total_bytes_sent < len(data):
        bytes_sent = socket.send(data[total_bytes_sent:])
        if bytes_sent == 0:
            raise RuntimeError("socket connection broken")
        total_bytes_sent += bytes_sent


def send_message(socket, message, timeout=None):
    """
    Prepare a message to send and send it.
    :param socket: The socket to receive with.
    :param message: The message to send in dictionary with bytes.
    :param timeout: If not set to None, the timeout in seconds
                    (not accurate use with caution only includes onc
                    the socket starts to send it will check for timeout)
    :raise TimeoutError: If socket timed out
    """
    socket.settimeout(timeout)
    socket.sendall(_pack_message(message))
