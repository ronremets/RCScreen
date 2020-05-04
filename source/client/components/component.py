"""
Base class for controlling components
"""
__author__ = "Ron Remets"

import logging
import threading
import time


class Component(object):
    """
    Base class for controlling components
    """
    def __init__(self):
        # TODO: is name needed?
        # TODO: name belongs to class an not the object
        self._name = "Component"  # The name of the component
        self._main_thread = None
        self._running_lock = threading.Lock()
        self._set_running(False)

    @property
    def running(self):
        """
        Check if the component is running
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
        self._setup()
        while self.running:
            time.sleep(0)
            self._update()

    def _update(self):
        """
        This is what the component does in every update
        """

    def _setup(self):
        """
        This is what the component does before starting, this runs in
        the same thread the self._update runs in
        """

    def _start(self):  # TODO: maybe rename to start_tracking
        """
        Create and start the main thread. Call this from sub class
        after configuring the components.
        """
        logging.info(f"Starting component {self._name}")
        self._set_running(True)
        self._main_thread = threading.Thread(
            name=f"Component {self._name} main thread",
            target=self._run)
        self._main_thread.start()

    def close(self, timeout=None):
        """
        Stop the component and close the threads
        :param timeout: the time is seconds to wait until all threads
                        close
        """
        logging.info(f"Closing {self._name}")
        self._set_running(False)
        if self._main_thread is not None:
            self._main_thread.join(timeout)
