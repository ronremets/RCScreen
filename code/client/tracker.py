"""
Base class for controlling components
"""
__author__ = "Ron Remets"

import logging
import threading


class Tracker(object):
    """
    Base class for controlling components
    """
    def __init__(self, name):
        self._name = name  # The name of the component
        self._main_thread = None
        self._running_lock = threading.Lock()
        self._set_running(False)

    @property
    def running(self):
        """
        Check if the tracker is running
        :return: True if it is, otherwise False
        """
        with self._running_lock:
            return self._running

    def _set_running(self, value):
        with self._running_lock:
            self._running = value

    def _run(self):
        """
        The main thread of the component. This runs the self._update
        function until component closes
        """
        while self.running:
            self._update()

    def _update(self):
        """
        This is what the component does in every update
        """

    def start(self):
        """
        Create and start the main thread. Call this from sub class
        after configuring the components.
        """
        logging.info(f"Starting {self._name}")
        self._set_running(True)
        self._main_thread = threading.Thread(target=self._run)
        self._main_thread.start()

    def close(self, block=True):
        """
        Stop the component and close the threads
        """
        logging.info(f"Closing {self._name}")
        self._set_running(False)
        if block and self._main_thread is not None:
            self._main_thread.join()
