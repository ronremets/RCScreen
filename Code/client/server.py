"""
Handles the communication to the server and the other client.
"""

__author__ = "Ron Remets"

import socket
import threading

SERVER_ADDRESS = ("127.0.0.1", 4567)
MESSAGE_PREFIX_LENGTH = 10
BUFFER_SIZE = 1024
ENCODING = "ASCII"
TIMEOUT = 2


class ServerClosedError(Exception):
    """
    Raised when the server closes
    """
    pass


class Server(object):
    """
    Communicates to the server
    """
    def __init__(self):
        self._socket = None
        self._received_packets = []
        self._packets_to_send = []
        self.update_recv_buffer_thread = None
        self.update_send_buffer_thread = None
        self._recv_lock = threading.Lock()
        self._send_lock = threading.Lock()
        self._running_lock = threading.Lock()
        self.running = False

    # noinspection PyMissingOrEmptyDocstring
    @property
    def running(self):
        with self._running_lock:
            return self.__running

    @running.setter
    def running(self, value):
        with self._running_lock:
            self.__running = value

    def _recv_fixed_length_data(self, length):
        """
        Receives a fixed length packet.
        :param length: The length of the packet.
        :return: The length of the packet
        :raise RuntimeError: If socket is closed from the other side.
        """
        data = b""
        bytes_received = 0
        while bytes_received < length:
            if not self.running:
                raise ServerClosedError("Server closed")
            try:
                data_chunk = self._socket.recv(
                    min(length - bytes_received, BUFFER_SIZE))
                if data_chunk == b"":
                    raise RuntimeError("socket connection broken")
                data += data_chunk
                bytes_received += len(data_chunk)
            except socket.timeout:
                pass
        return data

    def _recv_packet(self):
        """
        Receive a packet from the socket.
        :return: The packet in bytes
        :raise RuntimeError: If socket is closed from the other side.
        """
        length = int(self._recv_fixed_length_data(MESSAGE_PREFIX_LENGTH))
        packet = self._recv_fixed_length_data(length)
        return packet

    def _update_recv_buffer(self):
        """
        Update the recv buffer by adding received packets to it.
        """
        try:
            while self.running:
                packet = self._recv_packet()
                with self._recv_lock:
                    self._received_packets.append(packet)
        except ServerClosedError:
            pass

    def _send_raw_data(self, data):
        """
        Send a data
        :param data: The data to send
        :raise RuntimeError: If socket is closed from the other side.
        """
        total_bytes_sent = 0
        while total_bytes_sent < len(data):
            if not self.running:
                raise ServerClosedError("Server closed")
            try:
                bytes_sent = self._socket.send(data[total_bytes_sent:])
                if bytes_sent == 0:
                    raise RuntimeError("socket connection broken")
                total_bytes_sent += bytes_sent
            except socket.timeout:
                pass

    def _send_packet(self, packet):
        """
        Prepare a packet to send and send it.
        :param packet: The packet to send.
        """
        finished_packet = bytearray(
            str(len(packet)), ENCODING).zfill(MESSAGE_PREFIX_LENGTH) + packet
        self._send_raw_data(finished_packet)

    def _update_send_buffer(self):
        """
        Update the send buffer by sending packets from it.
        """
        try:
            while self.running:
                packet = None
                with self._send_lock:
                    if len(self._packets_to_send) > 0:
                        packet = self._packets_to_send.pop()
                if packet is not None:
                    self._send_packet(packet)
        except ServerClosedError:
            pass

    def send(self, packet):
        """
        Send a packet by adding it to the "packets to send" list.
        :param packet: The packet to send.
        """
        with self._send_lock:
            self._packets_to_send.append(packet)

    def recv(self):
        """
        Receive a packet from the "received packets" list. If none
        exists, return None
        :return: The packet received
        """
        with self._recv_lock:
            if len(self._received_packets) > 0:
                return self._received_packets.pop()
        return None  # Added for clarity

    def blocking_recv(self):
        """
        Block until a pocket is received and return it.
        :return: The packet received.
        """
        packet = self.recv()
        while packet is None:
            if not self.running:
                raise RuntimeError("Socket closed")
            packet = self.recv()
        return packet

    def connect(self):
        """
        Connect to client and open threads for read and write.
        """
        self._socket = socket.socket()
        self._socket.settimeout(TIMEOUT)
        self.update_recv_buffer_thread = threading.Thread(
            target=self._update_recv_buffer)
        self.update_send_buffer_thread = threading.Thread(
            target=self._update_send_buffer)
        self._socket.connect(SERVER_ADDRESS)
        self.running = True
        self.update_recv_buffer_thread.start()
        self.update_send_buffer_thread.start()

    def close(self, is_blocking):
        """
        Close the server.
        :param is_blocking: If true, wait for all the threads to stop.
        """
        self.running = False
        if is_blocking:
            if self.update_recv_buffer_thread.is_alive():
                self.update_recv_buffer_thread.join()
            if self.update_send_buffer_thread.is_alive():
                self.update_send_buffer_thread.join()
        self._socket.close()


def test(s, me):
    """
    test
    """
    me.connect()
    c, a = s.accept()
    try:
        p = b"hello world"
        p2 = (bytearray(str(len(p)), ENCODING).zfill(MESSAGE_PREFIX_LENGTH)
              + p)
        # print(p2)
        c.send(p2)
        print(me.blocking_recv())
        p = b"hello world"
        p2 = (bytearray(str(len(p)), ENCODING).zfill(MESSAGE_PREFIX_LENGTH)
              + p)
        c.send(p2)
        print(me.blocking_recv())
        me.send(b"Hello world")
        print(c.recv(1024))
    finally:
        me.close(True)
        c.close()


if __name__ == "__main__":
    server = Server()
    sock = socket.socket()
    sock.bind(SERVER_ADDRESS)
    sock.listen()
    try:
        print(1)
        test(sock, server,)
        print(2)
        test(sock, server)
    finally:
        sock.close()
