"""
A user
"""

__author__ = "Ron Remets"

import threading


class User(object):
    """
    A user
    """
    def __init__(self, username, password):
        self.username = username
        self.password = password
