"""
A controller that sends its information through a connection
"""
__author__ = "Ron Remets"

from kivy.properties import ObjectProperty, BooleanProperty

from controller import Controller
from communication.message import Message, MESSAGE_TYPES

CONTROLLER_INSTRUCTIONS = {
    "move left": "ml",
    "move right": "mr",
    "move up": "mu",
    "move down": "md",
    "click left": "cl",
    "press left": "pl",
    "release left": "rl",
    "click right": "cr",
    "press right": "pr",
    "release right": "rr"
}


class StreamedController(Controller):
    """
    A controller that sends its information through a connection
    """
    connection = ObjectProperty()
    is_active = BooleanProperty(False)

    def move_left(self):
        """
        Move to the left
        """
        if self.is_active:
            self.connection.socket.send(Message(
                MESSAGE_TYPES["controller"],
                CONTROLLER_INSTRUCTIONS["move left"]))

    def move_right(self):
        """
        Move to the right
        """
        if self.is_active:
            self.connection.socket.send(Message(
                MESSAGE_TYPES["controller"],
                CONTROLLER_INSTRUCTIONS["move right"]))

    def move_up(self):
        """
        Move up
        """
        if self.is_active:
            self.connection.socket.send(Message(
                MESSAGE_TYPES["controller"],
                CONTROLLER_INSTRUCTIONS["move up"]))

    def move_down(self):
        """
        Move down
        """
        if self.is_active:
            self.connection.socket.send(Message(
                MESSAGE_TYPES["controller"],
                CONTROLLER_INSTRUCTIONS["move down"]))

    def left_button_clicked(self):
        """
        Click the left button
        """
        if self.is_active:
            self.connection.socket.send(Message(
                MESSAGE_TYPES["controller"],
                CONTROLLER_INSTRUCTIONS["click left"]))

    def right_button_clicked(self):
        """
        Click the right button
        """
        if self.is_active:
            self.connection.socket.send(Message(
                MESSAGE_TYPES["controller"],
                CONTROLLER_INSTRUCTIONS["click right"]))

    def left_button_pressed(self):
        """
        Press the left button
        """
        if self.is_active:
            self.connection.socket.send(Message(
                MESSAGE_TYPES["controller"],
                CONTROLLER_INSTRUCTIONS["press left"]))

    def right_button_pressed(self):
        """
        Press the right button
        """
        if self.is_active:
            self.connection.socket.send(Message(
                MESSAGE_TYPES["controller"],
                CONTROLLER_INSTRUCTIONS["press right"]))

    def left_button_released(self):
        """
        Release the left button
        """
        if self.is_active:
            self.connection.socket.send(Message(
                MESSAGE_TYPES["controller"],
                CONTROLLER_INSTRUCTIONS["release left"]))

    def right_button_release(self):
        """
        Release the right button
        """
        if self.is_active:
            self.connection.socket.send(Message(
                MESSAGE_TYPES["controller"],
                CONTROLLER_INSTRUCTIONS["release right"]))
