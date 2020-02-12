"""
A action of the user database
"""

__author__ = "Ron Remets"


class Action(object):
    """
    An action for the user database
    """
    def __init__(self, command, parameters):
        self.command = command
        self.parameters = parameters
