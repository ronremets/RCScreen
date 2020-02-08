"""
a database class for users
"""

__author__ = "Ron Remets"

import traceback

import sqlite3

from data.user import User


class UsersDatabase(object):
    """
    A database class for users
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
                    "(id int AUTOINCREMENT(10),"
                    " username text UNIQUE,"
                    " password text,"
                    " PRIMARY KEY(id))\n")
            self._connection.commit()
        except Exception as e:
            print("Error:" + str(e))

    def add_user(self, username, password):
        """
        Add a user to the database. Only a unique username is allowed.
        :param username: The username of the user.
        :param password: The password of the user.
        """
        self._cursor.execute(
            "INSERT INTO users\n"
            "VALUES (?, ?)", (username, password))
        self._connection.commit()

    def get_user(self, username, password):
        """
        Get a user's details from the database.
        :param username: The username of the user.
        :param password: The password of the user.
        :return: A User object.
        """
        self._cursor.execute(
            "SELECT username, password FROM users\n"
            "WHERE username = ? and password = ?",
            (username, password))
        result = self._cursor.fetchone()
        if result is None:
            raise ValueError("No such user")
        return User(result[0], result[1])

    def delete_user(self, user):
        """
        Delete a user from the database.
        :param user: The user to delete.
        """
        self._cursor.execute(
            "DELETE FROM users\n"
            "WHERE username = ? and password = ?",
            (user.username, user.password))

    def get_all_usernames(self):
        """
        Get the usernames of all users in th database.
        :return: A list of all the usernames.
        """
        self._cursor.execute("SELECT username FROM users")
        usernames = self._cursor.fetchall()
        if usernames is not None:
            return [*usernames]
        # TODO: remove the print and check if [*usernames] can work for
        #  all cases
        print("None found")
        return []

    def close(self):
        """
        Close th database.
        """
        self._connection.close()
