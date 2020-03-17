"""
A message for communicating through sockets
"""

__author__ = "Ron Remets"

import communication_protocol

# The length of the length of the message content
MESSAGE_LENGTH_LENGTH = 16
MESSAGE_TYPE_LENGTH = 1  # The length of the type of the message
MESSAGE_TYPES = {
    "server interaction": "1",
    "controller": "2",
    "controlled": "3"
}


class Message(object):
    """
    A message  for communicating through sockets
    """
    def __init__(self, message_type, content):
        self.message_type = message_type
        self.content = content

    @property
    def content(self):
        """
        The content of the message not decoded
        :return: A bytes object with the content of the message
        """
        return self._content

    @content.setter
    def content(self, value):
        """
        Set the content of the message, if value is instance of str
        it will be encoded using communication_protocol.ENCODING
        :param value: The content of the message in bytes or str
        """
        if len(value) > 10 ** MESSAGE_LENGTH_LENGTH:
            raise ValueError(f"Message can not be longer than"
                             f" {MESSAGE_LENGTH_LENGTH}")
        if isinstance(value, str):
            self._content = value.encode(communication_protocol.ENCODING)
        else:
            self._content = value

    @property
    def message_type(self):
        """
        The type of the message. TODO: explain
        :return: A string with the type
        """
        return self._message_type

    @message_type.setter
    def message_type(self, value):
        """
        Set the type of the message
        :param value: he type of the message as str. TODO: explain
        """
        if len(value) > 10 ** MESSAGE_TYPE_LENGTH:
            raise ValueError(f"Message type can not be longer than"
                             f" {MESSAGE_TYPE_LENGTH}")
        self._message_type = value

    def get_content_as_text(self):
        """
        :return: The content decoded as text
        """
        return self.content.decode(communication_protocol.ENCODING)
