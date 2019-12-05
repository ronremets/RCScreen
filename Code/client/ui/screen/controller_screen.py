"""
The controller screen.
"""

__author__ = "Ron Remets"

import threading
import time
import io
import socket
import queue
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty, BooleanProperty, StringProperty
from kivy.uix.image import CoreImage
from kivy.clock import Clock
import PIL.ImageGrab
import PIL.Image

import communication_protocol

SERVER_ADDRESS = ("127.0.0.1", 2125)


class ControllerScreen(Screen):
    """
    The screen where the client controls another client.
    """
    screen = ObjectProperty()
    is_controller = BooleanProperty()
    code = StringProperty()
    other_code = StringProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._screen_update_event = None
        self._socket = None
        self._recv_packet_queue = queue.SimpleQueue()
        self._packet_to_send_queue = queue.SimpleQueue()
        self._recv_thread = None
        self._send_thread = None
        self._running = False
        self._running_lock = threading.Lock()

        self._input = None
        self._input_lock = threading.Lock()
        self._output = None
        self._output_lock = threading.Lock()

    @property
    def running(self):
        with self._running_lock:
            return self._running

    @running.setter
    def running(self, value):
        with self._running_lock:
            self._running = value

    def _recv_packets(self):
        while self.running:
            #try:
            #    self._recv_packet_queue.put(
            #        communication_protocol.recv_packet(self._socket))
            #except queue.Full:
            #    pass
            current_input = communication_protocol.recv_packet(self._socket)
            with self._input_lock:
                self._input = current_input

    def _send_messages(self):
        while self._running:
            #try:
            #    communication_protocol.send_message(
            #        self._socket,
            #        self._packet_to_send_queue.get())
            #except queue.Empty:
            #    pass
            with self._output_lock:
                output = self._output
            if output is not None:
                communication_protocol.send_message(
                    self._socket,
                    output)

    def _update_screen(self, *args):
        """
        Update the screen.
        """
        if self.is_controller:
            #try:
            with self._input_lock:
                image_bytes = self._input#self._recv_packet_queue.get()
            if image_bytes is not None:
                image_data = io.BytesIO(image_bytes)
                image_data.seek(0)
                texture = CoreImage(image_data, ext="png").texture
                self.screen.texture = texture
                self.screen.reload()
        #except queue.Empty:
            #    pass
        else:
            image = PIL.ImageGrab.grab()
            image_data = io.BytesIO()
            image.save(image_data, "png")
            image_data.seek(0)
            data = image_data.read()
            #try:
            #    self._packet_to_send_queue.put({"content": data})
            #except queue.Full:
            #    pass
            with self._output_lock:
                self._output = {"content": data}

    def on_enter(self, *args):
        """
        When this screen starts, start showing the screen.
        """
        print("other_code:", self.other_code)
        self._recv_thread = threading.Thread(target=self._recv_packets)
        self._send_thread = threading.Thread(target=self._send_messages)
        self._socket = socket.socket()
        self._socket.connect(SERVER_ADDRESS)
        communication_protocol.send_message(
            self._socket,
            {"content": f"{self.code}\n{self.other_code}".encode(
                communication_protocol.ENCODING)})
        # This suck change this
        # is bad dont it you have so much to live for
        # injection is inevitable (sql injection)
        self.running = True
        self._send_thread.start()
        self._recv_thread.start()
        self._screen_update_event = Clock.schedule_interval(
            self._update_screen, 0)

    def on_leave(self, *args):
        """
        When this screen stops, wait for screen to stop.
        """
        # self._screen_thread.join()
        self._screen_update_event.cancel()
        self.running = False
        self._recv_thread.join()
        self._send_thread.join()
