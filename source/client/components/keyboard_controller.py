"""
Controls the keyboard
"""
__author__ = "Ron Remets"

import time
import win32api
import win32con

from component import Component
OTHER_KEYCODES = {
    "backspace": win32con.VK_BACK,
    "tab": win32con.VK_TAB,
    "enter": win32con.VK_RETURN,
    "f15": win32con.VK_PAUSE,
    "capslock": win32con.VK_CAPITAL,
    "escape": win32con.VK_ESCAPE,
    "spacebar": win32con.VK_SPACE,
    "end": win32con.VK_END,
    "home": win32con.VK_HOME,
    "left": win32con.VK_LEFT,
    "up": win32con.VK_UP,
    "right": win32con.VK_RIGHT,
    "down": win32con.VK_DOWN,
    "f13": win32con.VK_PRINT,
    "insert": win32con.VK_INSERT,
    "delete": win32con.VK_DELETE,
    "numpad0": win32con.VK_NUMPAD0,
    "numpad1": win32con.VK_NUMPAD1,
    "numpad2": win32con.VK_NUMPAD2,
    "numpad3": win32con.VK_NUMPAD3,
    "numpad4": win32con.VK_NUMPAD4,
    "numpad5": win32con.VK_NUMPAD5,
    "numpad6": win32con.VK_NUMPAD6,
    "numpad7": win32con.VK_NUMPAD7,
    "numpad8": win32con.VK_NUMPAD8,
    "numpad9": win32con.VK_NUMPAD9,
    "f1": win32con.VK_F1,
    "f2": win32con.VK_F2,
    "f3": win32con.VK_F3,
    "f4": win32con.VK_F4,
    "f5": win32con.VK_F5,
    "f6": win32con.VK_F6,
    "f7": win32con.VK_F7,
    "f8": win32con.VK_F8,
    "f9": win32con.VK_F9,
    "f10": win32con.VK_F10,
    "f11": win32con.VK_F11,
    "f12": win32con.VK_F12,
    "numlock": win32con.VK_NUMLOCK,
    "f14": win32con.VK_SCROLL,
    "lshift": win32con.VK_LSHIFT,
    "rshift": win32con.VK_RSHIFT,
    "lctrl": win32con.VK_LCONTROL,
    "rctrl": win32con.VK_RCONTROL,
    "alt": win32con.VK_LMENU,
    "alt-gr": win32con.VK_RMENU,
}


class KeyboardController(Component):
    """
    Controls the keyboard
    """
    def __init__(self):
        super().__init__()
        self._connection = None

    def _handle_key_state(self, key, state):
        """
        Press or release a key
        :param key: The key to press as a string (following the kivy
                    library keycodes names)
        :param state: 'release' for releasing the key otherwise it will
                      be pressed.
        """
        flags = 0
        if state == "release":
            flags = win32con.KEYEVENTF_KEYUP
            print("releasing ")
        try:
            if len(key) == 1:
                keycode = win32api.VkKeyScan(key)
            else:
                keycode = OTHER_KEYCODES[key]
        except KeyError:
            # TODO: log bad key here
            pass
        else:
            print(f"key {key}")
            #win32api.keybd_event(keycode, 0, flags, 0)

    """def keyb(self,
             char=None,
             shift=False,
             control=False,
             alt=False,
             delaik=0.02):
        for b in char:
            c = b
            if 'A' <= b <= 'Z' or shift:
                win32api.keybd_event(win32con.VK_SHIFT, 0, 0, 0)
            if 'a' <= b <= 'z':
                c = b.upper()
            if alt:
                win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)
                time.sleep(0.250)
            if control:
                win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
            cord = ord(c)

            win32api.keybd_event(cord, 0, win32con.KEYEVENTF_EXTENDEDKEY | 0,
                                 0)
            if delaik > 0.0:
                time.sleep(delaik)
            win32api.keybd_event(cord, 0, win32con.KEYEVENTF_EXTENDEDKEY |
                                 win32con.KEYEVENTF_KEYUP, 0)
            if delaik > 0.0:
                time.sleep(delaik)

            if control:
                win32api.keybd_event(win32con.VK_CONTROL, 0,
                                     win32con.KEYEVENTF_KEYUP, 0)
            if alt:
                win32api.keybd_event(win32con.VK_MENU, 0,
                                     win32con.KEYEVENTF_KEYUP, 0)
                time.sleep(0.05)
            if 'A' <= b <= 'Z' or shift:
                win32api.keybd_event(win32con.VK_SHIFT, 0,
                                     win32con.KEYEVENTF_KEYUP, 0)"""

    def _update(self):
        message = self._connection.socket.recv(block=False)
        if message is not None:
            key, state = message.get_content_as_text().split(", ")
            self._handle_key_state(key, state)

    def start(self, connection):
        """
        Start the controller
        :param connection: The connection to get the info from.
        """
        self._connection = connection
        self._start()
