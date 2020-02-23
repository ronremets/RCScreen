"""
The entry point for the backend server.
"""

__author__ = "Ron Remets"

from server import Server
from users_database import UsersDatabase
import traceback

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
    except Exception as e:
        if server is not None:
            try:
                server.close()
            except Exception as closing_e:
                print("Error while closing server:")
                traceback.print_tb(closing_e)
        print("Error while running server:")
        traceback.print_tb(e)


if __name__ == "__main__":
    main()
