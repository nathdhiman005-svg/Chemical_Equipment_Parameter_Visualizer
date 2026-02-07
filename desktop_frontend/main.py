"""
main.py — Entry point for the PyQt5 Chemical Equipment Visualizer desktop app.
Login required — routes to Dashboard or Admin Panel based on user role.
"""

import sys
from PyQt5.QtWidgets import QApplication

from session_manager import SessionManager
from auth_window import AuthWindow
from dashboard_window import DashboardWindow
from admin_dashboard_window import AdminDashboardWindow
from admin_user_detail_window import AdminUserDetailWindow


class App:
    """Manages the auth → dashboard / admin flow."""

    def __init__(self):
        self.qapp = QApplication(sys.argv)
        self.qapp.setStyle("Fusion")
        self.session = SessionManager()

        # Windows — created on demand
        self.auth_win = None
        self.dash_win = None
        self.admin_win = None
        self.detail_win = None

        self._show_auth()

    # ── Window management ─────────────────────────────

    def _hide_all(self):
        for win in (self.auth_win, self.dash_win, self.admin_win, self.detail_win):
            if win:
                win.hide()

    def _show_auth(self):
        self._hide_all()
        self.auth_win = AuthWindow(self.session)
        self.auth_win.authenticated.connect(self._on_authenticated)
        self.auth_win.show()

    def _on_authenticated(self):
        self._hide_all()
        if self.session.is_superuser:
            self._show_admin()
        else:
            self._show_dashboard()

    def _show_dashboard(self):
        self._hide_all()
        self.dash_win = DashboardWindow(self.session)
        self.dash_win.logout_requested.connect(self._on_logout)
        if self.session.is_superuser:
            self.dash_win.admin_panel_requested.connect(self._show_admin)
        self.dash_win.show()

    def _show_admin(self):
        self._hide_all()
        self.admin_win = AdminDashboardWindow(self.session)
        self.admin_win.logout_requested.connect(self._on_logout)
        self.admin_win.user_selected.connect(self._show_user_detail)
        self.admin_win.set_dashboard_callback(self._show_dashboard)
        self.admin_win.show()

    def _show_user_detail(self, user_id):
        self._hide_all()
        self.detail_win = AdminUserDetailWindow(self.session, user_id)
        self.detail_win.back_requested.connect(self._show_admin)
        self.detail_win.show()

    def _on_logout(self):
        self.session.logout()
        self._show_auth()

    # ── Run ───────────────────────────────────────────

    def run(self):
        sys.exit(self.qapp.exec_())


if __name__ == "__main__":
    App().run()
