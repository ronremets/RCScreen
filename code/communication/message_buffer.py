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
    def __init__(self, buffered=True, maxsize=100):
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
        buffer will be dropped unless state did not change
        :param buffered: The state of the buffer. See the init for
                         detail.
        :param maxsize: when buffered, how many messages to store. If
                        set to 0 then buffer forever.
        """
        with self._messages_lock:
            if (self._buffered == buffered
                    and maxsize == self._messages.maxsize):
                return
            self._buffered = buffered
            if buffered:
                self._messages = queue.Queue(maxsize=maxsize)
            else:
                self._messages = None

    def add(self, message, timeout=None):
        """
        Add messages to buffer.
        :param message: The message to add.
        :param timeout: If not None and buffer is buffered, the time
                        while adding. If timeout occurs, raise
                        queue.Full
        :raise queue.Full: If timeout occurs and buffered
        """
        with self._messages_lock:
            if self._buffered:
                self._messages.put(message,
                                   block=timeout is None,
                                   timeout=timeout)
            else:
                self._messages = message

    def pop(self, timeout=None): # TODO: queue has timeout, use it
        """
        Get a message from the buffer.
        :param timeout: If not None and buffers is buffered, the amount
                        of time to wait before returning. If no message
                        added until timeout, return None.
        :return: The message and if there is not one, return None
        """
        with self._messages_lock:
            if self._buffered:
                if not self._messages.empty():
                    # no dead lock because otherwise it would not
                    # enter the if
                    return self._messages.get(timeout=timeout)
                return None
            if self._messages is None:
                return None
            message = self._messages
            self._messages = None
            return message

    def empty(self):
        """
        Check if the buffer is empty. Not reliable if multi threaded as
        Other threads can add items immediately after checking
        :return: True if nothing in buffer, False otherwise
        """
        with self._messages_lock:
            return self._messages.empty()
