"""
auth_window.py — Login / Register window for the PyQt5 desktop app.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTabWidget, QMessageBox,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont


class AuthWindow(QWidget):
    """Combined Login + Register tabs. Emits `authenticated` on success."""

    authenticated = pyqtSignal()

    def __init__(self, session):
        super().__init__()
        self.session = session
        self.setWindowTitle("Chemical Visualizer — Sign In")
        self.setFixedSize(420, 400)
        self._build_ui()

    # ── UI ─────────────────────────────────────────────

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)

        title = QLabel("⚗️ Chemical Visualizer")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setStyleSheet("color:#1a237e;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        layout.addSpacing(8)

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
        self.login_user.setPlaceholderText("Enter username")
        lay.addWidget(self.login_user)
        lay.addWidget(QLabel("Password"))
        self.login_pass = QLineEdit()
        self.login_pass.setPlaceholderText("Enter password")
        self.login_pass.setEchoMode(QLineEdit.Password)
        self.login_pass.returnPressed.connect(self._do_login)
        lay.addWidget(self.login_pass)
        btn = QPushButton("Login")
        btn.setStyleSheet(
            "background:#1a237e;color:#fff;padding:8px;border-radius:4px;font-size:14px;"
        )
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
        self.reg_pass2.returnPressed.connect(self._do_register)
        for field in (self.reg_user, self.reg_email, self.reg_company, self.reg_pass, self.reg_pass2):
            lay.addWidget(field)
        btn = QPushButton("Register")
        btn.setStyleSheet(
            "background:#1a237e;color:#fff;padding:8px;border-radius:4px;font-size:14px;"
        )
        btn.clicked.connect(self._do_register)
        lay.addWidget(btn)
        lay.addStretch()
        return w

    # ── Actions ────────────────────────────────────────

    def _do_login(self):
        username = self.login_user.text().strip()
        password = self.login_pass.text()
        if not username or not password:
            QMessageBox.warning(self, "Error", "Please fill in all fields.")
            return
        try:
            self.session.login(username, password)
            self.authenticated.emit()
        except Exception as exc:
            QMessageBox.warning(self, "Login Failed", str(exc))

    def _do_register(self):
        if self.reg_pass.text() != self.reg_pass2.text():
            QMessageBox.warning(self, "Error", "Passwords do not match.")
            return
        if not self.reg_user.text().strip() or not self.reg_pass.text():
            QMessageBox.warning(self, "Error", "Username and password are required.")
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
