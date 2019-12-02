"""
Responsible for switching screens.
"""

__author__ = "Ron Remets"

from kivy.uix.screenmanager import ScreenManager
from kivy.properties import BooleanProperty, StringProperty


class WindowManager(ScreenManager):
    """
    Handles switching screens.
    """
    is_controller = BooleanProperty(False)
    code = StringProperty()
    other_code = StringProperty()
