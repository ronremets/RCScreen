"""
A message for communicating through sockets
"""
__author__ = "Ron Remets"

# The encoding used in the protocol.
ENCODING = "UTF-8"
# The length of the length of the message content.
MESSAGE_LENGTH_LENGTH = 16
# The length of the type of the message.
MESSAGE_TYPE_LENGTH = 1
# The type of message (use to know what to expect in the message)
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

    def __repr__(self):
        length = len(self.content)
        try:
            content_to_print = self.content.decode(ENCODING)
        except UnicodeError:
            content_to_print = f"{length} unprintable bytes"
        else:
            if length > 1000:
                content_to_print = f"{length} bytes"
        return "\n".join((f"Length: {length}",
                          f"Type: {self.message_type}",
                          f"Content: {content_to_print}"))

    @property
    def content(self):
        """
        The content of the message not decoded
        :return: A bytes object with the content of the message
        """
        return self._content

    @content.setter
    def content(self, content):
        """
        Set the content of the message, if value is instance of str
        it will be encoded using communication_protocol.ENCODING
        :param content: The content of the message in bytes or str
        """
        if len(content) > 10 ** MESSAGE_LENGTH_LENGTH:
            raise ValueError(f"Message can not be longer than "
                             f"{MESSAGE_LENGTH_LENGTH}")
        if isinstance(content, str):
            self._content = content.encode(ENCODING)
        else:
            self._content = content

    @property
    def message_type(self):
        """
        The type of the message.
        :return: A string with the type
        """
        return self._message_type

    @message_type.setter
    def message_type(self, message_type):
        """
        Set the type of the message
        :param message_type: The type of the message as str.
        """
        # TODO: should this check or assume?
        if message_type not in MESSAGE_TYPES.values():
            raise ValueError(
                f"Message type {message_type} does not exists")
        elif len(message_type) > 10 ** MESSAGE_TYPE_LENGTH:
            raise ValueError("Message type can not be longer than "
                             f"{MESSAGE_TYPE_LENGTH}")
        self._message_type = message_type

    def get_content_as_text(self):
        """
        :return: The content decoded as text
        """
        return self.content.decode(ENCODING)
