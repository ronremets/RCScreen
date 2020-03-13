"""
A controller for mouse movement
"""
__author__ = "Ron Remets"

from kivy.uix.relativelayout import RelativeLayout
from kivy.properties import ObjectProperty, BooleanProperty

from client.mouse import Mouse


class Controller(RelativeLayout):
    """
    A controller for mouse movement
    """
    left_click_button = ObjectProperty()
    left_click_button_toggled = BooleanProperty(False)
    right_click_button = ObjectProperty()
    right_click_button_toggled = BooleanProperty(False)
    left_button = ObjectProperty()
    right_button = ObjectProperty()
    up_button = ObjectProperty()
    down_button = ObjectProperty()
    mouse = ObjectProperty(Mouse())

    def move_mouse_left(self):
        """
        Move the mouse to the left
        """
        x = self.mouse.x
        dx = self.mouse.x_sensitivity
        if x - dx >= 0:
            self.mouse.x = x - dx
        else:
            self.mouse.x = 0

    def move_mouse_right(self):
        """
        Move the mouse to the right
        """
        x = self.mouse.x
        dx = self.mouse.x_sensitivity
        max_x = self.get_root_window().width
        if x + dx <= max_x:
            self.mouse.x = x + dx
        else:
            self.mouse.x = max_x

    def move_mouse_up(self):
        """
        Move up the mouse
        """
        y = self.mouse.y
        dy = self.mouse.y_sensitivity
        if y - dy >= 0:
            self.mouse.y = y - dy
        else:
            self.mouse.y = 0

    def move_mouse_down(self):
        """
        Move down the mouse
        """
        y = self.mouse.y
        dy = self.mouse.y_sensitivity
        max_y = self.get_root_window().height
        if y + dy <= max_y:
            self.mouse.y = y + dy
        else:
            self.mouse.y = max_y

    def left_mouse_button_pressed(self):
        """
        Press or release the left button of the mouse
        """
        if self.left_click_button_toggled:
            self.mouse.left_button = "released"
        else:
            self.mouse.left_button = "pressed"
        self.left_click_button_toggled = not self.left_click_button_toggled

    def right_mouse_button_pressed(self):
        """
        Press the right button of the mouse
        """
        if self.right_click_button_toggled:
            self.mouse.right_button = "released"
        else:
            self.mouse.right_button = "pressed"
        self.right_click_button_toggled = not self.right_click_button_toggled
