"""
Makes tokens for connections
"""
__author__ = "Ron Remets"

import time
import random
import threading


class TokenGenerator(object):
    """
    Makes tokens for connections
    """
    def __init__(self):
        # TODO: add expiration date cus if too many connections create
        #  tokens and then crash, the tokens wont be removed and fill up
        #  the memory
        self._tokens = {}
        self._token_index = 0
        self._tokens_lock = threading.Lock()
        self._token_index_lock = threading.Lock()

    def _create_token(self):
        """
        Create a token.
        :return: The token as bytes.
        """
        # TODO: make this hash function better
        with self._token_index_lock:
            self._token_index += 1
            return (str(int(time.time()) ^ random.randint(1000, 9999))
                    + str(self._token_index)).encode("ascii")

    def generate(self, username, connection_name):
        """
        Generate a token for a user's connection.
        :param username: The username of the user that generated the
                         token.
        :param connection_name: The name of the connection of the user
                                that generated the token.
        :return: The token as bytes
        """
        token = self._create_token()
        with self._tokens_lock:
            self._tokens[token] = (username, connection_name)
        return token

    def release_token(self, token, username, connection_name):
        """
        Using valid credentials, remove the token from the generator.
        :param token: The token to check.
        :param username: The username of the user that wants to release
                         the token.
        :param connection_name: The name of the connection of the user
                                that wants to release the token.
        :raise KeyError: If token does not exists.
        :raise ValueError: If username or connection name is wrong.
        """
        try:
            with self._tokens_lock:
                real_username, real_connection_name = self._tokens[token]
                if (username == real_username
                        and connection_name == real_connection_name):
                    # This cannot crash since otherwise
                    # self._tokens[token] would have crashed.
                    self._tokens.pop(token)
                else:
                    raise ValueError(
                        "Token's username or connection name is wrong")
        except KeyError:
            raise ValueError("Token does not exists")
