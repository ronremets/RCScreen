"""
A class to store the clients data.
"""

__author__ = "Ron Remets"

import threading
import queue

import communication_protocol


class Client(object):
    """
    Stores clients data.
    """
    def __init__(self, socket, code, other_code):
        self._socket = socket
        self.__code = code
        self.__other_code = other_code
        self._message_queue = queue.Queue(maxsize=1)
        self._send_thread = threading.Thread(
            target=self._send_messages_to_client)
        self._recv_thread = threading.Thread(
            target=self._recv_messages_from_client)
        self._finish_starting_thread = threading.Thread(
            target=self._finish_starting)
        self._running_lock = threading.Lock()
        self._code_lock = threading.Lock()
        self._other_code_lock = threading.Lock()
        self._other_client_lock = threading.Lock()
        self.other_client = None
        self._set_running(True)

        self._finish_starting_thread.start()

    @property
    def code(self):
        with self._code_lock:
            return self.__code

    @property
    def other_code(self):
        with self._other_code_lock:
            return self.__other_code

    @property
    def running(self):
        with self._running_lock:
            return self.__running

    @property
    def other_client(self):
        with self._other_client_lock:
            return self.__other_client

    @other_client.setter
    def other_client(self, other_client):
        with self._other_client_lock:
            self.__other_client = other_client

    def _set_running(self, value):
        with self._running_lock:
            self.__running = value

    def _finish_starting(self):
        """
        Wait for other client and then finish starting
        """
        while self.other_client is None and self.running:
            pass
        if self.running:
            self._send_thread.start()
            self._recv_thread.start()

    def add_message(self, message):
        """
        Wrapper for self._message_queue.put(message)
        :param message: The message to add to client
        """
        try:
            self._message_queue.put(message)
        except queue.Full:
            pass

    def _send_messages_to_client(self):
        while self.running:
            try:
                message = self._message_queue.get()
                communication_protocol.send_message(
                    self._socket,
                    message)
            except queue.Empty:
                pass

    def _recv_messages_from_client(self):
        while self.running:
            content = communication_protocol.recv_packet(self._socket)
            self.other_client.add_message({"content": content})

    def __repr__(self):
        return (f"socket: {self._socket}\n"
                f"code: {self.code}\n"
                f"other_code: {self.other_code}"
                f"other_client: {type(self.other_client)}")

    def close(self, kill=True):
        """
        Close the client.
        :param kill: kill all the threads without joining
        """
        self._set_running(False)
        if kill:
            self._finish_starting_thread.join()
            self._recv_thread.join()
            self._send_thread.join()
        self._socket.close()
