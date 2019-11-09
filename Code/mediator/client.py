"""
A class to store the clients data.
"""

__author__ = "Ron Remets"


class Client(object):
    """
    Stores clients data.
    """
    def __init__(self, socket, code, other_code):
        self._socket = socket
        self._code = code
        self._other_code = other_code

    def __repr__(self):
        return (f"socket: {self._socket}\n"
                f"code: {self._code}\n"
                f"other_code: {self._other_code}")

    def close(self):
        """
        Close the client.
        """
        self._socket.close()
