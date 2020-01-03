"""
The protocol used for the socket communication.
"""

__author__ = "Ron Remets"

import lz4.frame

from message import Message, MESSAGE_LENGTH_LENGTH, MESSAGE_TYPE_LENGTH

BUFFER_SIZE = 1024  # The buffer size used when receiving and sending.
ENCODING = "ASCII"  # The encoding used in the protocol.


def _pack_message(message):
    """
    Pack a message object to bytes.
    :return: The message in bytes.
    """
    packed_content = lz4.frame.compress(message.content)
    length = len(packed_content)
    packet = (
            str(length).zfill(
                MESSAGE_LENGTH_LENGTH).encode(ENCODING)
            + str(message.message_type).zfill(
                MESSAGE_TYPE_LENGTH).encode(ENCODING)
            + message.content)
    return packet


def _recv_fixed_length_data(socket, length):
    """
    Receives a fixed length packet from a socket.
    :param socket: The socket to receive with.
    :param length: The length of the packet.
    :return: The length of the packet
    :raise RuntimeError: If socket is closed from the other side.
    """
    data = b""
    bytes_received = 0
    while bytes_received < length:
        data_chunk = socket.recv(min(length - bytes_received, BUFFER_SIZE))
        if data_chunk == b"":
            raise RuntimeError("socket connection broken")
        data += data_chunk
        bytes_received += len(data_chunk)
    return data


def recv_message(socket):
    """
    Receive a packet from a socket.
    :param socket: The socket to receive with.
    :return: The packet in bytes
    :raise RuntimeError: If socket is closed from the other side.
    """
    message_type = _recv_fixed_length_data(socket, MESSAGE_TYPE_LENGTH)
    length = int(_recv_fixed_length_data(socket, MESSAGE_LENGTH_LENGTH))
    content = lz4.frame.decompress(_recv_fixed_length_data(socket, length))
    return Message(message_type, content)


def _send_raw_data(socket, data):
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


def send_message(socket, message):
    """
    Prepare a message to send and send it.
    :param socket: The socket to receive with.
    :param message: The message to send in dictionary with bytes.
    """
    _send_raw_data(socket, _pack_message(message))
