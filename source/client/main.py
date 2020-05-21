"""
This is the entry point of the client's application.
"""
__author__ = "Ron Remets"

import logging

from RC_screen_app import RCScreenApp

logging.basicConfig(level=logging.DEBUG)


def main():
    """
    Start the application
    """
    RCScreenApp().run()


if __name__ == '__main__':
    main()
