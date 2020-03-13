"""
a database class for users
"""

__author__ = "Ron Remets"

import traceback
import threading

import sqlite3


class UsersDatabase(object):
    """
    A database class for users
    """
    def __init__(self, db_file_name):
        self._connection = sqlite3.connect(db_file_name)
        self._cursor = self._connection.cursor()

    @staticmethod
    def create_database(db_file_name):
        try:
            connection = sqlite3.connect(db_file_name)
            cursor = connection.cursor()
            cursor.execute(
                "CREATE TABLE IF NOT EXISTS users\n"
                "(password TEXT, "
                "username TEXT UNIQUE, "
                "id INTEGER PRIMARY KEY)\n")
            connection.commit()
            connection.close()
        except Exception:
            print("Database error:")
            traceback.print_exc()

    def add_user(self, username, password):
        """
        Add a user to the database. Only a unique username is allowed.
        :param username: The username of the user.
        :param password: The password of the user.
        """
        self._cursor.execute(
            "INSERT INTO users(username, password)\n"
            "VALUES (?, ?)", (username, password))
        self._connection.commit()

    def get_user(self, username, password):
        """
        Get a user's details from the database.
        :param username: The username of the user.
        :param password: The password of the user.
        :return: The username and password.
        """
        self._cursor.execute(
            "SELECT username, password FROM users\n"
            "WHERE username = ? and password = ?",
            (username, password))
        result = self._cursor.fetchone()
        if result is None:
            raise ValueError("No such user")
        return result[0], result[1]

    def delete_user(self, username, password):
        """
        Delete a user from the database.
        :param username: The username of the user to delete.
        :param password: The password of the user to delete
        """
        self._cursor.execute(
            "DELETE FROM users\n"
            "WHERE username = ? and password = ?",
            (username, password))
        self._connection.commit()

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

    def user_exists(self, username):
        """
        CHeck if a user exists
        :param username: The username of the user
        :return: True if exists False otherwise
        """
        self._cursor.execute("SELECT username FROM users\n"
                             "WHERE username = ?", (username,))
        return self._cursor.fetchone() is None

    def close(self):
        """
        Close the database.
        """
        self._connection.close()
