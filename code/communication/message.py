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
        return self.__content

    @content.setter
    def content(self, value):
        if len(value) > 10 ** MESSAGE_LENGTH_LENGTH:
            raise ValueError(f"Message can not be longer than"
                             f" {MESSAGE_LENGTH_LENGTH}")
        self.__content = value

    @property
    def message_type(self):
        return self.__message_type

    @message_type.setter
    def message_type(self, value):
        if len(value) > 10 ** MESSAGE_TYPE_LENGTH:
            raise ValueError(f"Message type can not be longer than"
                             f" {MESSAGE_TYPE_LENGTH}")
        self.__message_type = value

    def get_content_as_text(self):
        """
        :return: The content decoded as text
        """
        return self.content.decode(communication_protocol.ENCODING)
