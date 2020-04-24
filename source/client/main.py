"""
This is the entry point of the client's application.
"""
__author__ = "Ron Remets"

import logging

from RC_screen_app import RCScreenApp

# Tree("D:\\Programming\\Python\\RCScreen\\source\\client\\components"),
# Tree("D:\\Programming\\Python\\RCScreen\\source\\client\\ui\\screen", prefix="screen"),
# Tree("D:\\Programming\\Python\\RCScreen\\source\\client\\ui\\popup", prefix="popup"),
# Tree("D:\\Programming\\Python\\RCScreen\\source\\client\\ui", prefix="ui", excludes=["screen", "popup"]),
# Tree("D:\\Programming\\Python\\RCScreen\\source\\client", excludes=["components", "ui"]),
# Tree("D:\\Programming\\Python\\RCScreen\\source\\communication", prefix="communication"),
# Tree("C:\\Program Files\\Python37\\Lib\\site-packages\\lz4", prefix='lz4'),
# Tree("C:\\Program Files\\Python37\\Lib\\site-packages\\PIL", prefix="PIL"),

logging.basicConfig(level=logging.DEBUG)


def main():
    """
    Start the application
    """
    RCScreenApp().run()


if __name__ == '__main__':
    main()
