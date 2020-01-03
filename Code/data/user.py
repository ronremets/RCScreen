"""
A class to store user data
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
