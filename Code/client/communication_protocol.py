"""
The protocol used for the socket communication.
"""

__author__ = "Ron Remets"

MESSAGE_PREFIX_LENGTH = 100  # The length of the prefix of the data.
BUFFER_SIZE = 1024  # The buffer size used when receiving and sending.
ENCODING = "ASCII"  # The encoding used in the protocol.


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


def recv_packet(socket):
    """
    Receive a packet from a socket.
    :param socket: The socket to receive with.
    :return: The packet in bytes
    :raise RuntimeError: If socket is closed from the other side.
    """
    length = int(_recv_fixed_length_data(socket, MESSAGE_PREFIX_LENGTH))
    packet = _recv_fixed_length_data(socket, length)
    return packet


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
    print(message)
    packet = (
        f"{len(message['content'])}".zfill(
            MESSAGE_PREFIX_LENGTH).encode(ENCODING)
        + message['content'])
    _send_raw_data(socket, packet)
