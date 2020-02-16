"""
The entry point for the backend server.
"""

__author__ = "Ron Remets"

from server import Server
import traceback


def main():
    """
    The entry point of the server application.
    """
    server = None
    try:
        server = Server()
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
