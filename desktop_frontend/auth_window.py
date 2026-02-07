"""
auth_window.py — Login / Register window for the PyQt5 desktop app.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTabWidget, QMessageBox,
)
from PyQt5.QtCore import Qt, pyqtSignal


class AuthWindow(QWidget):
    """Combined Login + Register tabs. Emits `authenticated` on success."""

    authenticated = pyqtSignal()

    def __init__(self, session):
        super().__init__()
        self.session = session
        self.setWindowTitle("Chemical Visualizer — Sign In")
        self.setFixedSize(400, 360)
        self._build_ui()

    # ── UI ─────────────────────────────────────────────

    def _build_ui(self):
        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        tabs.addTab(self._login_tab(), "Login")
        tabs.addTab(self._register_tab(), "Register")
        layout.addWidget(tabs)

    def _login_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(10)
        lay.addWidget(QLabel("Username"))
        self.login_user = QLineEdit()
        lay.addWidget(self.login_user)
        lay.addWidget(QLabel("Password"))
        self.login_pass = QLineEdit()
        self.login_pass.setEchoMode(QLineEdit.Password)
        lay.addWidget(self.login_pass)
        btn = QPushButton("Login")
        btn.clicked.connect(self._do_login)
        lay.addWidget(btn)
        lay.addStretch()
        return w

    def _register_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(8)
        self.reg_user = QLineEdit(); self.reg_user.setPlaceholderText("Username")
        self.reg_email = QLineEdit(); self.reg_email.setPlaceholderText("Email")
        self.reg_company = QLineEdit(); self.reg_company.setPlaceholderText("Company (optional)")
        self.reg_pass = QLineEdit(); self.reg_pass.setPlaceholderText("Password"); self.reg_pass.setEchoMode(QLineEdit.Password)
        self.reg_pass2 = QLineEdit(); self.reg_pass2.setPlaceholderText("Confirm Password"); self.reg_pass2.setEchoMode(QLineEdit.Password)
        for field in (self.reg_user, self.reg_email, self.reg_company, self.reg_pass, self.reg_pass2):
            lay.addWidget(field)
        btn = QPushButton("Register")
        btn.clicked.connect(self._do_register)
        lay.addWidget(btn)
        lay.addStretch()
        return w

    # ── Actions ────────────────────────────────────────

    def _do_login(self):
        try:
            self.session.login(self.login_user.text().strip(), self.login_pass.text())
            self.authenticated.emit()
        except Exception as exc:
            QMessageBox.warning(self, "Login Failed", str(exc))

    def _do_register(self):
        if self.reg_pass.text() != self.reg_pass2.text():
            QMessageBox.warning(self, "Error", "Passwords do not match.")
            return
        try:
            self.session.register(
                self.reg_user.text().strip(),
                self.reg_email.text().strip(),
                self.reg_pass.text(),
                self.reg_pass2.text(),
                self.reg_company.text().strip(),
            )
            self.authenticated.emit()
        except Exception as exc:
            QMessageBox.warning(self, "Registration Failed", str(exc))
