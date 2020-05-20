"""
A mouse
"""
__author__ = "Ron Remets"

import time

from kivy.app import App
from kivy.graphics import Rectangle, Color
from kivy.uix.widget import Widget
from kivy.core.window import Window
from kivy.properties import (ObjectProperty,
                             BooleanProperty,
                             NumericProperty,
                             OptionProperty)

from communication.message import Message, MESSAGE_TYPES

DEFAULT_BUTTON_TYPE = "left"
DEFAULT_CLICK_TYPE = "move"
DEFAULT_MOUSE_INSIDE_SPRITE_PERCENT = 0.9
MOUSE_OUTSIDE_COLOR = 0, 0, 0, 1
MOUSE_INSIDE_COLOR = 1, 1, 1, 1


class Mouse(Widget):
    """
    A mouse
    """
    # Decides which button the double tap activates
    button_type = OptionProperty(DEFAULT_BUTTON_TYPE,
                                 options=["left", "right"])
    # Decides Whether taps and move press the mouse or move them.
    # Double tap always clicks the mouse
    click_type = OptionProperty(DEFAULT_CLICK_TYPE,
                                options=["move", "click"])
    connection = ObjectProperty()
    is_tracking = BooleanProperty(False)
    sprite_inside_percent = NumericProperty(
        DEFAULT_MOUSE_INSIDE_SPRITE_PERCENT,
        min=0,
        max=1)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._app = App.get_running_app()
        with self.canvas:
            Color(*MOUSE_OUTSIDE_COLOR)
            self.sprite_outside = Rectangle(pos=self.pos, size=self.size)
            Color(*MOUSE_INSIDE_COLOR)
            self.sprite_inside = Rectangle(pos=self.pos, size=self.size)

        self.bind(pos=self.update_sprite)
        self.bind(size=self.update_sprite)

    def update_sprite(self, *args):
        x, y = self.pos
        width, height = self.size
        inside_x = x + ((width - width * self.sprite_inside_percent) / 2)
        inside_y = y + ((height - height * self.sprite_inside_percent) / 2)
        self.sprite_inside.pos = inside_x, inside_y
        self.sprite_inside.size = (width * self.sprite_inside_percent,
                                   height * self.sprite_inside_percent)
        self.sprite_outside.pos = self.pos
        self.sprite_outside.size = self.size

    def _transform_pos(self, pos):
        """
        Turn the position of the widget on this screen to the position
        of the mouse in the other screen
        :param pos: The current position of the mouse
        :return: The transformed position
        """
        # Note that the screens' pos is (0, 0) and are the size of the
        # windows. Therefor, touch is always inside the screen
        other_width = self._app.other_screen_width
        other_height = self._app.other_screen_height
        width, height = self._app.screen_size
        # TODO: use screen pos and not divide by.
        #  what if image is not centered?
        dy = pos[1] - (Window.height - height) / 2
        dx = pos[0] - (Window.width - width) / 2
        if width == 0:
            transformed_x = 0
        else:
            transformed_x = int((dx / width) * other_width)
        if height == 0:
            transformed_y = 0
        else:
            transformed_y = int(other_height - (dy / height) * other_height)
        return transformed_x, transformed_y

    def on_touch_down(self, touch):
        print("MOUSE EXISTS")
        if not self.is_tracking:
            return super().on_touch_down(touch)
        print("MOUSE WORKS")
        self.pos = touch.pos
        if touch.is_double_tap:
            action = "click"
        elif self.click_type == "move":
            action = "move"
        else:
            action = "press"
        x, y = self._transform_pos(touch.pos)
        self.connection.socket.send(Message(
            MESSAGE_TYPES["controller"],
            f"{action} {self.button_type} {x},{y}"))
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        """
        Happens every frame while touch is down
        :param touch: The touch object
        """
        if not self.is_tracking:
            return False
        self.pos = touch.pos

    def on_touch_up(self, touch):
        if not self.is_tracking:
            return False
        self.pos = touch.pos
        if self.click_type == "move":
            action = "move"
        else:
            action = "release"
        x, y = self._transform_pos(touch.pos)
        self.connection.socket.send(Message(
            MESSAGE_TYPES["controller"],
            f"{action} {self.button_type} {x},{y}"))
