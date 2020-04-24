"""
a database class for users
"""

__author__ = "Ron Remets"

import logging

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
        """
        create the database.
        :param db_file_name: The name of the file that will be created.
        """
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
            logging.error("Database error:", exc_info=True)

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
        # TODO: Get username return password of check if user exists
        #  and return bool or dont use this function.
        self._cursor.execute(
            "SELECT username, password FROM users\n"
            "WHERE username = ? and password = ?",
            (username, password))
        result = self._cursor.fetchone()
        if result is None:
            raise ValueError("No such user")
        return result[0], result[1]

    def get_password(self, username):
        """
        Get the password of a username.
        :param username: The username to get the password of.
        :return: The password of the username as a string.
        """
        self._cursor.execute(
            "SELECT password FROM users\n"
            "WHERE username = ?",
            (username,))
        result = self._cursor.fetchone()
        if result is None:
            raise ValueError("No such user")
        return result[0]

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
        results = self._cursor.fetchall()  # TODO: is this string?
        if results is not None:  # TODO: why not None? add checks and errors
            usernames = []
            for result in results:
                usernames.append(result[0])
            return usernames
        # TODO: remove the log and check if [*usernames] can work for
        #  all cases
        logging.warning("No users found")
        return []

    def username_exists(self, username):
        """
        CHeck if a username exists
        :param username: The username of the user
        :return: True if exists False otherwise
        """
        self._cursor.execute("SELECT username FROM users\n"
                             "WHERE username = ?", (username,))
        return self._cursor.fetchone() is not None

    def close(self):
        """
        Close the database.
        """
        self._connection.close()
