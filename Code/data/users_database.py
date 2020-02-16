"""
a database class for users
"""

__author__ = "Ron Remets"

import traceback
import threading
import queue

import sqlite3

from data.user import User


class UsersDatabase(object):
    """
    A database class for users
    """
    def __init__(self, db_file_name):
        self._command_index = 0
        self._connection = None
        self._cursor = None
        self._command_index_lock = threading.Lock()
        self._running_lock = threading.Lock()
        self._queries_lock = threading.Lock()
        self._results_lock = threading.Lock()
        self._queries = queue.Queue()
        self._results = queue.Queue()
        self._database_thread = threading.Thread(
            target=self._handle_queries, args=(db_file_name,))
        self._database_thread.start()

    @property
    def running(self):
        with self._running_lock:
            return self.__running

    def _set_running(self, value):
        self.__running = value

    def _connect_to_database(self, db_file_name):
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
                    "(id int,"
                    " username text UNIQUE,"
                    " password text,"
                    " PRIMARY KEY(id))\n")
            self._connection.commit()
        except Exception:
            print("Database error:")
            traceback.print_exc()

    def _add_user(self, username, password):
        """
        Add a user to the database. Only a unique username is allowed.
        :param username: The username of the user.
        :param password: The password of the user.
        """
        self._cursor.execute(
            "INSERT INTO users\n"
            "VALUES (?, ?)", (username, password))
        self._connection.commit()

    def _get_user(self, username, password):
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

    def _delete_user(self, user):
        """
        Delete a user from the database.
        :param user: The user to delete.
        """
        self._cursor.execute(
            "DELETE FROM users\n"
            "WHERE username = ? and password = ?",
            (user.username, user.password))

    def _get_all_usernames(self):
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

    def _user_exists(self, username):
        """
        CHeck if a user exists
        :param username: The username of the user
        :return: True if exists False otherwise
        """
        self._cursor.execute("SELECT username FROM users\n"
                             "WHERE username = ?", (username,))
        return self._cursor.fetchone() is None

    def _close(self):
        """
        Close the database.
        """
        self._connection.close()

    def add_user(self, username, password):
        with self._command_index_lock:
            index = self._command_index
            self._command_index += 1
        self._add_command((index, self._add_user, (username, password)))

    def _add_command(self, command):
        with self._queries_lock:
            self._queries.put(command)

    def _handle_queries(self, db_file_name):
        """
        The main loop of the database object. Get and handle queries.
        """
        self._connect_to_database(db_file_name)
        self._set_running(True)
        while self.running:
            with self._queries_lock:
                index, action, args = self._queries.get()
            result = action(*args)
            with self._results_lock:
                self._results.put(result)





