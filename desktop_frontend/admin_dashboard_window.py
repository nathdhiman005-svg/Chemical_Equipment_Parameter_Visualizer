"""
admin_dashboard_window.py — Admin panel: user list with search, opens user detail.
"""

from datetime import datetime

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QTableWidget, QTableWidgetItem, QMessageBox,
    QGroupBox, QHeaderView,
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor


class AdminDashboardWindow(QMainWindow):
    """Lists all users with real-time search. Clicking a row opens detail view."""

    logout_requested = pyqtSignal()
    user_selected = pyqtSignal(int)  # emits user_id

    def __init__(self, session):
        super().__init__()
        self.session = session
        self.users_data = []
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(300)
        self._search_timer.timeout.connect(self._do_search)
        self.setWindowTitle("Admin Panel — Chemical Visualizer")
        self.setMinimumSize(900, 600)
        self._build_ui()
        self._refresh_users()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 12, 16, 12)

        # ── Header row ──
        header_row = QHBoxLayout()
        username = self.session.user.get("username", "Admin") if self.session.user else "Admin"
        title = QLabel(f"Admin Panel: {username}")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setStyleSheet("color:#1a237e;")
        header_row.addWidget(title)
        header_row.addStretch()

        btn_dash = QPushButton("My Dashboard")
        btn_dash.setStyleSheet(
            "background:#1565c0;color:#fff;padding:6px 16px;border-radius:4px;font-size:13px;"
        )
        btn_dash.clicked.connect(self._go_dashboard)
        header_row.addWidget(btn_dash)

        btn_logout = QPushButton("Logout")
        btn_logout.setStyleSheet(
            "background:#e53935;color:#fff;padding:6px 16px;border-radius:4px;font-size:13px;"
        )
        btn_logout.clicked.connect(self._do_logout)
        header_row.addWidget(btn_logout)
        root.addLayout(header_row)

        subtitle = QLabel("Manage all registered users and their data uploads")
        subtitle.setStyleSheet("color:#666;font-size:12px;margin-bottom:8px;")
        root.addWidget(subtitle)

        # ── Search bar ──
        search_group = QGroupBox("Search Users")
        search_lay = QHBoxLayout(search_group)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by username or email…")
        self.search_input.setStyleSheet("padding:8px;font-size:13px;")
        self.search_input.textChanged.connect(self._on_search_changed)
        search_lay.addWidget(self.search_input)
        root.addWidget(search_group)

        # ── User table (5 columns: ID, Username, Email, Registration Date, Action) ──
        self.user_table = QTableWidget(0, 5)
        self.user_table.setHorizontalHeaderLabels(
            ["ID", "Username", "Email", "Registration Date", ""]
        )
        header = self.user_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.user_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.user_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.user_table.cellClicked.connect(self._on_row_clicked)
        self.user_table.setStyleSheet(
            "QTableWidget::item:selected { background: #e3f2fd; color: #1a237e; }"
        )
        root.addWidget(self.user_table, stretch=1)

        # Hint
        hint = QLabel("Click a user row or the View button to see their full upload history.")
        hint.setStyleSheet("color:#888;font-size:11px;margin-top:4px;")
        root.addWidget(hint)

    # ── Data ──────────────────────────────────────────

    def _refresh_users(self, search=""):
        try:
            self.users_data = self.session.admin_get_users(search)
        except Exception as exc:
            QMessageBox.warning(self, "Error", f"Failed to load users:\n{exc}")
            self.users_data = []
        self._fill_table()

    def _fill_table(self):
        self.user_table.setRowCount(len(self.users_data))
        for i, u in enumerate(self.users_data):
            self.user_table.setItem(i, 0, QTableWidgetItem(str(u["id"])))

            name_text = u["username"]
            if u.get("is_superuser"):
                name_text += "  [ADMIN]"
            name_item = QTableWidgetItem(name_text)
            if u.get("is_superuser"):
                name_item.setForeground(QColor("#e53935"))
            self.user_table.setItem(i, 1, name_item)

            self.user_table.setItem(i, 2, QTableWidgetItem(u.get("email") or "—"))

            date_str = u.get("date_joined", "—")
            if date_str and date_str != "—":
                try:
                    dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    date_str = dt.strftime("%b %d, %Y")
                except Exception:
                    pass
            self.user_table.setItem(i, 3, QTableWidgetItem(date_str))

            # View button
            user_id = u["id"]
            btn_view = QPushButton("View Details")
            btn_view.setStyleSheet(
                "background:#1a237e;color:#fff;padding:4px 14px;"
                "border-radius:3px;font-size:12px;"
            )
            btn_view.setCursor(Qt.PointingHandCursor)
            btn_view.clicked.connect(lambda _, uid=user_id: self.user_selected.emit(uid))
            self.user_table.setCellWidget(i, 4, btn_view)

    # ── Search ────────────────────────────────────────

    def _on_search_changed(self):
        self._search_timer.start()

    def _do_search(self):
        self._refresh_users(self.search_input.text().strip())

    # ── Row interaction ───────────────────────────────

    def _on_row_clicked(self, row, _col):
        if 0 <= row < len(self.users_data):
            user_id = self.users_data[row]["id"]
            self.user_selected.emit(user_id)

    # ── Navigation ────────────────────────────────────

    def _go_dashboard(self):
        """Signal the app to show the regular dashboard."""
        self.hide()
        self._show_dashboard_signal()

    def _show_dashboard_signal(self):
        """Placeholder — App connects this via a callback."""
        pass

    def set_dashboard_callback(self, callback):
        self._show_dashboard_signal = callback

    def _do_logout(self):
        self.session.logout()
        self.logout_requested.emit()
