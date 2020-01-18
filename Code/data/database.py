"""
a database class
"""

__author__ = "Ron Remets"

import traceback

import sqlite3


class Database(object):
    """
    A database class
    """
    def __init__(self, db_file_name):
        try:
            self._connection = sqlite3.connect(db_file_name)
            self._cursor = self._connection.cursor()

            self._cursor.execute(
                'SELECT name FROM sqlite_master WHERE type = "table"')
            tables = self._cursor.fetchall()
            print(tables)
            if "users" not in map(lambda x: x[0], tables):
                self._cursor.execute(
                    "CREATE TABLE users\n"
                    "(username date, password text)\n")
            self._connection.commit()
        except Exception as e:
            print("Error:" + str(e))

    def add_user(self, user):
        """
        Add a user to the database. only one username is allowed
        :param user: The user to add
        """
        pass

    def close(self):
        """
        Close th database.
        """
        self._connection.close()



Database("mama.db")
