"""
A class to store the clients data.
"""

__author__ = "Ron Remets"

import threading

import communication_protocol


class Client(object):
    """
    Stores clients data.
    """
    def __init__(self, socket, code, other_code):
        self.socket = socket
        self.__code = code
        self.__other_code = other_code
        self.__running = True
        self._message_list = []
        self._send_thread = threading.Thread(
            target=self._send_messages_to_client)
        self._recv_thread = threading.Thread(
            target=self._recv_messages_from_client)
        self._running_lock = threading.Lock()
        self._message_list_lock = threading.Lock()
        self._code_lock = threading.Lock()
        self._other_code_lock = threading.Lock()
        self.other_client = None

        self._send_thread.start()
        self._recv_thread.start()

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

    def add_message(self, message):
        print("entering message lock")
        with self._message_list_lock:
            print("passed message lock")
            print("adding message " + str(type(message)))
            self._message_list.append(message)

    def _send_messages_to_client(self):
        while self.running:
            with self._message_list_lock:
                # print(self.other_client)
                for message in self._message_list[:]:
                    print("sending message to client: " + str(type(message)))
                    communication_protocol.send_message(
                        self.socket,
                        message)
                    self._message_list.remove(message)

    def _recv_messages_from_client(self):
        while self.running:
            content = communication_protocol.recv_packet(self.socket)
            print("this is the shit: " + str(content) + "\nother_client = " + str(self.other_client))
            if self.other_client is not None:
                self.other_client.add_message({"content": content})

    def __repr__(self):
        return (f"socket: {self.socket}\n"
                f"code: {self.code}\n"
                f"other_code: {self.other_code}")

    def close(self, block=True):
        """
        Close the client.
        """
        with self._running_lock:
            self.__running = False
        if block:
            self._recv_thread.join()
            self._send_thread.join()
        self.socket.close()
