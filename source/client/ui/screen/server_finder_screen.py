"""
The screen where you decide to which server to connect
"""
__author__ = "Ron Remets"

from kivy.uix.screenmanager import Screen
from kivy.app import App

from popup.error_popup import ErrorPopup


class ServerFinderScreen(Screen):
    """
    The screen where you decide to which server to connect
    """
    def _start_connection_manager(self, ip, port):
        app = App.get_running_app()
        try:
            port = int(port)
        except ValueError:
            error_popup = ErrorPopup()
            error_popup.content_label.text = "Port must be a number"
            error_popup.open()
        except Exception as e:
            error_popup = ErrorPopup()
            error_popup.content_label.text = str(e)
            error_popup.open()
        else:
            app.connection_manager.start((ip, port))
            self.manager.transition.direction = "right"
            app.root.current = "login"
