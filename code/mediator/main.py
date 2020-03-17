"""
The entry point for the backend server.
"""

__author__ = "Ron Remets"

import logging
import traceback

from server import Server
from users_database import UsersDatabase

logging.basicConfig(level=logging.DEBUG)
DB_FILE_NAME = "users.db"


def main():
    """
    The entry point of the server application.
    """
    server = None
    try:
        UsersDatabase.create_database(DB_FILE_NAME)
        server = Server(DB_FILE_NAME)
        server.start()
        input()
    except Exception:
        if server is not None:
            try:
                server.close()
            except Exception:
                logging.error("Error while closing server:", exc_info=True)
        logging.critical("Error while running server:", exc_info=True)


if __name__ == "__main__":
    main()
