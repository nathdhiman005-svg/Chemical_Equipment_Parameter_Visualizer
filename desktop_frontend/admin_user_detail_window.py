"""
admin_user_detail_window.py — Shows a specific user's info and full upload history.
Matches the web app layout: 3-column info grid, full upload table with actions.
"""

from datetime import datetime

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTableWidget, QTableWidgetItem, QMessageBox,
    QGroupBox, QHeaderView, QFileDialog, QFrame, QGridLayout,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont


class AdminUserDetailWindow(QMainWindow):
    """Displays full user info + complete upload history for admins."""

    back_requested = pyqtSignal()

    def __init__(self, session, user_id):
        super().__init__()
        self.session = session
        self.user_id = user_id
        self.user_info = None
        self.uploads = []
        self.setWindowTitle("User Detail — Admin Panel")
        self.setMinimumSize(950, 700)
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 12, 16, 12)

        # ── Back button ──
        btn_back = QPushButton("← Back to Admin Panel")
        btn_back.setStyleSheet(
            "background:none;color:#1a237e;border:none;font-size:13px;"
            "text-align:left;padding:4px 0;"
        )
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.clicked.connect(self._go_back)
        root.addWidget(btn_back)

        # ── User info card (title + 3-column grid like the web app) ──
        self.info_group = QGroupBox()
        self.info_group.setStyleSheet(
            "QGroupBox{background:#fff;border-radius:8px;padding:16px;"
            "border:1px solid #e0e0e0;}"
        )
        self.info_layout = QVBoxLayout(self.info_group)
        self.info_layout.setContentsMargins(16, 12, 16, 12)

        self.detail_title = QLabel("User Detail")
        self.detail_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.detail_title.setStyleSheet("color:#1a237e;border:none;")
        self.info_layout.addWidget(self.detail_title)
        self.info_layout.addSpacing(8)

        # 3-column grid for info cards (matches web: 3 cols × 2 rows)
        self.info_grid = QGridLayout()
        self.info_grid.setSpacing(12)
        self.info_layout.addLayout(self.info_grid)
        root.addWidget(self.info_group)

        # ── Uploads section ──
        uploads_group = QGroupBox()
        uploads_group.setStyleSheet(
            "QGroupBox{background:#fff;border-radius:8px;padding:16px;"
            "border:1px solid #e0e0e0;}"
        )
        uploads_lay = QVBoxLayout(uploads_group)
        uploads_lay.setContentsMargins(16, 12, 16, 12)

        self.uploads_title = QLabel("Complete Upload History")
        self.uploads_title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        self.uploads_title.setStyleSheet("color:#1a237e;border:none;")
        uploads_lay.addWidget(self.uploads_title)

        self.uploads_count_label = QLabel("")
        self.uploads_count_label.setStyleSheet(
            "color:#555;font-size:12px;font-weight:normal;border:none;"
        )
        uploads_lay.addWidget(self.uploads_count_label)

        self.uploads_table = QTableWidget(0, 5)
        self.uploads_table.setHorizontalHeaderLabels(
            ["ID", "File Name", "Rows Imported", "Uploaded At", "Actions"]
        )
        header = self.uploads_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.uploads_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.uploads_table.setStyleSheet("border:none;")
        uploads_lay.addWidget(self.uploads_table)
        root.addWidget(uploads_group, stretch=1)

    def _load_data(self):
        try:
            data = self.session.admin_get_user_uploads(self.user_id)
            self.user_info = data.get("user", {})
            self.uploads = data.get("uploads", [])
        except Exception as exc:
            QMessageBox.warning(self, "Error", f"Failed to load user data:\n{exc}")
            return
        self._fill_user_info()
        self._fill_uploads()

    def _make_info_card(self, label, value, is_password=False):
        """Create an info card matching the web app's infoItem style."""
        frame = QFrame()
        frame.setStyleSheet(
            "QFrame{background:#f5f5ff;border-radius:6px;border:none;}"
        )
        frame.setMinimumHeight(70)
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(4)

        lbl = QLabel(label.upper())
        lbl.setFont(QFont("Segoe UI", 9))
        lbl.setStyleSheet("color:#888;font-weight:normal;border:none;")
        lay.addWidget(lbl)

        if is_password:
            val = QLabel("••••••••••• (hashed)")
            val.setFont(QFont("Consolas", 11))
            val.setStyleSheet("color:#888;letter-spacing:2px;border:none;")
        else:
            val = QLabel(str(value))
            val.setFont(QFont("Segoe UI", 13, QFont.Bold))
            val.setStyleSheet("color:#1a237e;font-weight:600;border:none;")
        val.setWordWrap(True)
        lay.addWidget(val)
        lay.addStretch()
        return frame

    def _fill_user_info(self):
        # Clear existing cards from grid
        while self.info_grid.count():
            item = self.info_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        u = self.user_info
        date_str = u.get("date_joined", "—")
        if date_str and date_str != "—":
            try:
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                date_str = dt.strftime("%b %d, %Y %I:%M %p")
            except Exception:
                pass

        # 3 columns × 2 rows — same layout as web app
        cards = [
            ("Username", u.get("username", "—"), False),
            ("Email", u.get("email") or "—", False),
            ("Registration Date", date_str, False),
            ("Company", u.get("company") or "—", False),
            ("Role", u.get("role") or "—", False),
            ("Password", "", True),
        ]
        for idx, (label, value, is_pw) in enumerate(cards):
            row = idx // 3
            col = idx % 3
            self.info_grid.addWidget(
                self._make_info_card(label, value, is_password=is_pw), row, col
            )

        self.detail_title.setText(f"User Detail: {u.get('username', '')}")
        self.setWindowTitle(f"User Detail: {u.get('username', '')} — Admin Panel")

    def _fill_uploads(self):
        count = len(self.uploads)
        self.uploads_count_label.setText(
            f"{count} file{'s' if count != 1 else ''} uploaded — full history (no limit)"
        )
        self.uploads_table.setRowCount(count)
        for i, h in enumerate(self.uploads):
            self.uploads_table.setItem(i, 0, QTableWidgetItem(str(h["id"])))
            self.uploads_table.setItem(i, 1, QTableWidgetItem(h["file_name"]))
            self.uploads_table.setItem(i, 2, QTableWidgetItem(str(h["rows_imported"])))

            date_str = h.get("uploaded_at", "—")
            if date_str and date_str != "—":
                try:
                    dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    date_str = dt.strftime("%b %d, %Y %I:%M %p")
                except Exception:
                    pass
            self.uploads_table.setItem(i, 3, QTableWidgetItem(date_str))

            # Action buttons
            actions_widget = QWidget()
            actions_lay = QHBoxLayout(actions_widget)
            actions_lay.setContentsMargins(2, 2, 2, 2)
            actions_lay.setSpacing(4)

            upload_id = h["id"]

            btn_dl = QPushButton("Download")
            btn_dl.setStyleSheet(
                "background:#1565c0;color:#fff;padding:4px 10px;border-radius:3px;font-size:11px;"
            )
            btn_dl.clicked.connect(lambda _, uid=upload_id: self._download_report(uid))
            actions_lay.addWidget(btn_dl)

            btn_del = QPushButton("Delete")
            btn_del.setStyleSheet(
                "background:#e53935;color:#fff;padding:4px 10px;border-radius:3px;font-size:11px;"
            )
            btn_del.clicked.connect(lambda _, uid=upload_id: self._delete_upload(uid))
            actions_lay.addWidget(btn_del)

            self.uploads_table.setCellWidget(i, 4, actions_widget)

    # ── Actions ───────────────────────────────────────

    def _download_report(self, upload_id):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Report", "equipment_report.pdf", "PDF (*.pdf)"
        )
        if not path:
            return
        try:
            self.session.admin_download_report(path, upload_id)
            QMessageBox.information(self, "Report Saved", f"Report saved to:\n{path}")
        except Exception as exc:
            QMessageBox.warning(self, "Download Failed", str(exc))

    def _delete_upload(self, upload_id):
        reply = QMessageBox.question(
            self, "Confirm Delete",
            "Delete this upload and all its data?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        try:
            self.session.admin_delete_upload(upload_id)
            self.uploads = [u for u in self.uploads if u["id"] != upload_id]
            self._fill_uploads()
        except Exception as exc:
            QMessageBox.warning(self, "Delete Failed", str(exc))

    def _go_back(self):
        self.back_requested.emit()
