"""
The entry point for the backend server.
"""

__author__ = "Ron Remets"

import logging
import sys
import traceback
import threading
import queue

from server import Server
from users_database import UsersDatabase

logging.basicConfig(level=logging.DEBUG)
DB_FILE_NAME = "users.db"
COMMAND_PREFIX = "_command_"


def _get_commands():
    """
    Get a list of all commands
    :return: The list of strings of all commands
    """
    return [x[len(COMMAND_PREFIX):]
            for x in globals()
            if x.startswith(COMMAND_PREFIX)]


def _command_check_server_status(server):
    """
    Check if the server is running and print the result
    :param server: The server to check
    :return: Whether to close the server
    """
    logging.info(f"MAIN:Showing server status")
    print("Server status: ", end="")
    if not server.running:
        print("not ", end="")
    print("running")
    return False


def _command_shutdown_server(server):
    """
    Close server threads
    :param server: The server to shutdown
    :return: Whether to close the server
    """
    print("Type the timeout for shutdown. Type 'None' to not use timeout")
    timeout = input()
    if timeout.lower() != "none":
        try:
            timeout = float(timeout)
        except ValueError as e:
            print(e)  # TODO: remove
            logging.error("Input was not a number, aborting shutdown")
            print("Please enter a number or None. Aborting shutdown.")
            return False
    else:
        timeout = None

    logging.info(f"MAIN:Shutting down server")
    try:
        server.shutdown(timeout=timeout)
    except Exception:
        logging.critical("MAIN:Error while Shutting down server:",
                         exc_info=True)
    else:
        logging.info(f"MAIN:Shut down server")
    return False


def _command_close_server(server):
    """
    Close the server
    :param server: The server to close
    :return: Whether to close the server
    """
    if server.running:
        print("You should use 'shutdown_server' before 'close_server'"
              "to close the server properly\nType yes to continue")
        if input() != "yes":
            logging.info(f"MAIN:Aborting closing server")
            print("Aborting closing")
            return False
    logging.info(f"MAIN:Closing server")
    try:
        server.close()
    except Exception:
        logging.critical("MAIN:Error while closing server:", exc_info=True)
    else:
        logging.info(f"MAIN:Closed server")
    return True


def _command_quick_close(server):
    """
    Shutdown and then close the server. Abort on any error!
    :param server: The server to close.
    :return: Whether to close the server
    """
    try:
        if not _command_shutdown_server(server):
            _command_close_server(server)
    except Exception:
        logging.critical("MAIN:Error while quick closing server:",
                         exc_info=True)
    return True


def _command_help(_):
    """
    Display help message.
    :return: Whether to close the server
    """
    logging.info(f"MAIN:Displaying help")
    print("Commands:", _get_commands())
    return False


def _start_server(server):
    """
    Start the server
    :param server: The server to start
    """
    try:
        UsersDatabase.create_database(DB_FILE_NAME)
        server.start()
    except OSError as e:
        if e.errno == 10048:
            print("The port the server uses is already used.\n"
                  "Make sure only one server is running and that other apps "
                  "are not using this port.\n"
                  "It might help to reset the computer.")
        logging.error("MAIN:Error while creating server!",
                      exc_info=True)
    except Exception:
        logging.error("MAIN:Error while running server:", exc_info=True)


def main():
    """
    The entry point of the server application.
    """
    server = Server()
    logging.info("MAIN:Starting server")
    _start_server(server)
    logging.info("MAIN:Started server")
    commands = _get_commands()
    logging.info(f"MAIN:Available commands: {commands}")
    print("Type help for list of commands")
    while True:
        command = input()
        if command not in commands:  # Stop injections (maybe)
            print("Command not found")
        else:
            # TODO: this is a bad idea
            close_program = eval(f"{COMMAND_PREFIX}{command}(server)")
            if close_program:
                break


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logging.critical("MAIN:Error while running:", exc_info=True)
        sys.exit(1)
    else:
        sys.exit(0)
