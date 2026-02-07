"""
main.py — Entry point for the PyQt5 Chemical Equipment Visualizer desktop app.
No login required — connects directly to the API.
"""

import sys
from PyQt5.QtWidgets import QApplication

from session_manager import SessionManager
from dashboard_window import DashboardWindow


class App:
    """Launches directly into the dashboard (no auth)."""

    def __init__(self):
        self.qapp = QApplication(sys.argv)
        self.qapp.setStyle("Fusion")
        self.session = SessionManager()
        self.dash_win = DashboardWindow(self.session)
        self.dash_win.show()

    def run(self):
        sys.exit(self.qapp.exec_())


if __name__ == "__main__":
    App().run()
