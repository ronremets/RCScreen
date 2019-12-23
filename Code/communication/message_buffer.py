"""
A buffer for storing messages
"""

__author__ = "Ron Remets"

import threading
import queue


class MessageBuffer(object):
    """
    A buffer for storing messages
    """
    def __init__(self, buffered, maxsize=0):
        """
        :param buffered: The state of the buffer:
                      True - buffer the messages until you
                             reach maxsize if maxsize = 0 then buffer
                             forever.
                      False - only store the latest message,
                              maxsize will not matter.
        :param maxsize: when buffered, how many messages to store. If
                        set to 0 then buffer forever.
        """
        self._messages = None
        self._buffered = None
        self._messages_lock = threading.Lock()
        self.switch_state(buffered, maxsize)

    def switch_state(self, buffered, maxsize=0):
        """
        Switch the state of the buffer. All current messages in the
        buffer will be dropped.
        :param buffered: The state of the buffer. See the init for
                         detail.
        :param maxsize: when buffered, how many messages to store. If
                        set to 0 then buffer forever.
        """
        with self._messages_lock:
            self._buffered = buffered
            if buffered:
                self._messages = queue.Queue(maxsize=maxsize)
            else:
                self._messages = None

    def add(self, message):
        """
        Add messages to buffer.
        :param message: The message to add.
        """
        with self._messages_lock:
            if self._buffered:
                self._messages.put(message)
            else:
                self._messages = message

    def pop(self):
        """
        Get a message from the buffer.
        :return: The message
        """
        with self._messages_lock:
            if self._buffered:
                return self._messages.pop()
            else:
                if self._messages is None:
                    raise queue.Empty("Buffer is empty")
                message = self._messages
                self._messages = None
                return message
