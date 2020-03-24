"""
An image that constantly changes trough a socket
"""
__author__ = "Ron Remets"

import io
import threading

from kivy.clock import Clock
from kivy.properties import ObjectProperty, StringProperty
from kivy.core.image import Image as CoreImage
from kivy.uix.image import Image
from kivy.graphics.texture import Texture
from kivy.core.window import Window
from kivy.base import EventLoop

from communication.message import Message, MESSAGE_TYPES



class StreamedImage(Image):
    """
    An image that constantly changes trough a socket
    """
    frame = ObjectProperty()
    image_format = StringProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._socket = None
        self._update_frame_event = None
        self._receive_frame_thread = None
        self._frame = None
        self._frame_is_new = False
        self._streamed_image_format = "png"  # TODO: find default
        self._frame_is_new_lock = threading.Lock()
        self._frame_lock = threading.Lock()
        self._running_lock = threading.Lock()
        self._set_running(False)

    @property
    def running(self):
        """
        :return: If the server is running.
        """
        with self._running_lock:
            return self._running

    def _set_running(self, value):
        with self._running_lock:
            self._running = value

    def _receive_frame(self):
        """
        Receive frame and update the frame variable
        """
        #core_image = None
        while self.running:
            print("recv")
            frame_bytes = self._socket.recv().content
            # Make sure server does not send any packets until we are
            # ready to receive so it does not fill the network buffer
            self._socket.send(Message(MESSAGE_TYPES["controller"],
                                      "Message received"))
            print("update: ", len(frame_bytes))
            frame_data = io.BytesIO(frame_bytes)
            frame_data.seek(0)
            #CoreImage(frame_data,
            #          ext=self._streamed_image_format)
            #if core_image is None:
            #    core_image = CoreImage(frame_data,
            #                           ext=self._streamed_image_format)
            #else:
            #    core_image.load_memory(frame_data,
            #                           ext=self._streamed_image_format)
            #frame = core_image.texture

            print("frame lock")
            with self._frame_lock:
                #self.texture.blit_buffer(frame_bytes,
                #                         colorfmt='rgb',
                #                         bufferfmt='ubyte')\
                self._frame = frame_data

            print("new frame")
            with self._frame_is_new_lock:
                self._frame_is_new = True

            print("end")

    #def _reload_frame(self, texture):
    #    #from kivy.core.window import Window
    #    print("changing texture")
    #    texture.blit_buffer(self._frame,
    #                        bufferfmt="ubyte",
    #                        colorfmt="rgb")

   # def reload_image(self, _):


    def _update_frame(self, *_):
        """
        Update the image to the new frame
        """
        # If frame is new self._frame_is_new will remain true until
        # this threads sets it to false or the stream is closed.
        # In both cases the frame will remain new even if we exit the
        # lock
        with self._frame_is_new_lock:
            if not self._frame_is_new:
                return
            self._frame_is_new = False
        with self._frame_lock:
            frame = self._frame
        print("creating core")

        self.texture = CoreImage(frame,
                                 ext=self._streamed_image_format).texture
        #frame = self._frame
        #arr = bytearray(len(frame))
        #for i in range(len(frame)):
        #    arr[i] = frame[i]
        #EventLoop.ensure_window()
        print("reloading")
        self.reload()
        print(f"STREAMED IMAGE: Updated")
        #self.texture.reload()
        #print("scheduling")
        #Clock.schedule_once(self.reload_image)
        #self.reload()
        #self.texture.blit_buffer(self._frame,
        #                         bufferfmt="ubyte",
        #                         colorfmt="rgb")

        #EventLoop.ensure_window()
        #print(f"buffer format: {self.texture.bufferfmt}") # ubyte
        #print(f"color format: {self.texture.colorfmt}")



    def start(self, socket, image_format):
        """
        Start streaming
        :param socket: The socket to use to stream
        :param image_format: The format od the image
        """
        # TODO: https://buildmedia.readthedocs.org/media/pdf/kivy/latest/kivy.pdf
        #  page 360
        #self.texture = Texture.create(size=(720, 480),
        #                              bufferfmt="ubyte",
        #                              colorfmt="rgb")
        #self.texture.add_reload_observer(self._reload_frame)
        self._frame = None
        self._streamed_image_format = image_format
        print(f"image format is : {self._streamed_image_format}")
        self._frame_is_new = False
        self._socket = socket
        self._receive_frame_thread = threading.Thread(
            target=self._receive_frame)

        self._set_running(True)
        self._receive_frame_thread.start()
        print('a'*50 + "scheduling")
        from kivy.core.window import Window
        self._update_frame_event = Clock.schedule_interval(self._update_frame,
                                                           0)

    def close(self, timeout=None):
        """
        Close connections and stop streaming
        :param timeout: If not None, the timout to join on the
                        connection's thread
        :raise: TimeoutError: On timeout (still closes socket)
        """
        self._set_running(False)
        try:
            if self._receive_frame_thread is not None:
                self._receive_frame_thread.join(timeout)
            if self._update_frame_event is not None:
                self._update_frame_event.cancel()
        finally:
            if self._socket is not None:
                self._socket.close() #TODO: timeout
