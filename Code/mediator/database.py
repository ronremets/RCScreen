"""
Runs an sqlite3 database
"""

__author__ = "Ron Remets"

import sqlite3
import threading
import traceback


class Database(object):
    """
    Runs an sqlite3 database
    """
    def __init__(self, db_filename):
        self._connection = None
        self._cursor = None
        self._query_index = 0
        self._queries = dict()
        self._results = dict()
        self._query_index_lock = threading.Lock()
        self._running_lock = threading.Lock()
        self._queries_lock = threading.Lock()
        self._results_lock = threading.Lock()
        self._database_thread = threading.Thread(
            target=self._run_database, args=(db_filename,))

        self._set_running(False)
        self._database_thread.start()

    @property
    def running(self):
        """
        :return: Whether the database is running
        """
        with self._running_lock:
            return self.__running

    def _set_running(self, value):
        self.__running = value

    def _connect_database(self, db_filename):
        self._connection = sqlite3.connect(db_filename)
        self._cursor = self._connection.cursor()

    def _run_query(self, query):
        pass

    def _run_database(self, db_filename):
        self._connect_database(db_filename)
        self._set_running(True)
        while self.running:
            with self._queries_lock:
                index, query = self._queries.items()
            self._run_query()
