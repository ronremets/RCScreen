"""
A connection designed for connecting and disconnecting other connections
"""
__author__ = "Ron Remets"

import queue

from communication.connection import Connection


class Connector(Connection):
    """
    A connection designed for connecting and disconnecting other
     connections
    """
    def __init__(self, name, socket, connection_type):
        super().__init__(name, socket, connection_type)
        self.commands = queue.Queue()

    @staticmethod
    def parse_connector_command(command):
        """
        Parse and return the arguments of the command.
        :param command: The string to parse.
        :return: The arguments of the command
        """
        instruction = command[:command.index(":")]
        name = command[command.index(":") + 1:]
        return instruction, name
