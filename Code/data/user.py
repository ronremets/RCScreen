"""
A class to store user data
TODO: Is this even necessary? The user database functions can not just
  crash/return True and False/other way?
"""

__author__ = "Ron Remets"


class User(object):
    """
    A user
    """
    def __init__(self, username, password):
        self.username = username
        self.password = password

    def __eq__(self, other):
        return (self.username == other.username
                and self.password == other.password)
