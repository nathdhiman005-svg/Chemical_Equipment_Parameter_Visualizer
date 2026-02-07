"""
dashboard_window.py — Main dashboard with Matplotlib charts embedded in PyQt5.
Select-to-View workflow: Upload → File List → Analysis (hidden until a file is selected).
Charts are generated dynamically based on whatever numeric columns the CSV contained.
"""

import os
import numpy as np
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem,
    QSplitter, QGroupBox, QScrollArea, QFrame, QHeaderView,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


COLORS = ["#1a237e", "#0d47a1", "#1565c0", "#1e88e5", "#42a5f5", "#64b5f6", "#90caf9", "#bbdefb"]
ATTR_PALETTE = [
    "#1a237e", "#0d47a1", "#1565c0", "#2e7d32", "#e65100",
    "#6a1b9a", "#c62828", "#00695c", "#4e342e", "#37474f",
]


class DashboardWindow(QMainWindow):
    """Dashboard: Upload → File List (Show / Download PDF / Delete) → Analysis."""

    logout_requested = pyqtSignal()
    admin_panel_requested = pyqtSignal()

    def __init__(self, session):
        super().__init__()
        self.session = session
        self.selected_file_id = None
        self.file_stats = None
        self.history_data = []
        self._attr_canvases = []  # dynamic attribute chart canvases

        username = session.user.get("username", "User") if session.user else "User"
        self.setWindowTitle(f"Chemical Equipment Visualizer — {username}")
        self.setMinimumSize(1100, 850)
        self._build_ui()
        self._refresh_history()

    # ── UI Construction ───────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        # ═══ 0. HEADER BAR (user info + logout) ═══
        header_row = QHBoxLayout()
        username = self.session.user.get("username", "User") if self.session.user else "User"
        greeting = QLabel(f"Welcome, {username}")
        greeting.setFont(QFont("Segoe UI", 12, QFont.Bold))
        greeting.setStyleSheet("color:#1a237e;")
        header_row.addWidget(greeting)
        header_row.addStretch()

        if self.session.is_superuser:
            btn_admin = QPushButton("Admin Panel")
            btn_admin.setStyleSheet(
                "background:#ff6f00;color:#fff;padding:6px 16px;border-radius:4px;font-size:13px;"
            )
            btn_admin.clicked.connect(self._go_admin)
            header_row.addWidget(btn_admin)

        btn_logout = QPushButton("Logout")
        btn_logout.setStyleSheet(
            "background:#e53935;color:#fff;padding:6px 16px;border-radius:4px;font-size:13px;"
        )
        btn_logout.clicked.connect(self._do_logout)
        header_row.addWidget(btn_logout)
        root.addLayout(header_row)

        # ═══ 1. UPLOAD SECTION (top) ═══
        upload_group = QGroupBox("Upload CSV")
        upload_lay = QHBoxLayout(upload_group)
        btn_upload = QPushButton("Select && Upload CSV")
        btn_upload.setStyleSheet("background:#1a237e;color:#fff;padding:8px 20px;border-radius:4px;font-size:13px;")
        btn_upload.clicked.connect(self._upload_csv)
        upload_lay.addWidget(btn_upload)
        upload_lay.addStretch()
        root.addWidget(upload_group)

        # ═══ 2. UPLOADED FILES LIST (middle) ═══
        files_group = QGroupBox("Uploaded Files")
        files_lay = QVBoxLayout(files_group)
        self.hint_label = QLabel(
            "Click Show on a file to view its analysis below.\n"
            "Only the 5 most recent uploads are kept. Older uploads are automatically deleted."
        )
        self.hint_label.setFont(QFont("Segoe UI", 9))
        self.hint_label.setStyleSheet("color:#666;")
        self.hint_label.setWordWrap(True)
        files_lay.addWidget(self.hint_label)

        self.history_table = QTableWidget(0, 6)
        self.history_table.setHorizontalHeaderLabels(["File", "Rows", "Date", "", "", ""])
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        files_lay.addWidget(self.history_table)
        root.addWidget(files_group)

        # ═══ 3. FILE ANALYSIS (bottom — hidden until a file is selected) ═══
        self.analysis_widget = QWidget()
        analysis_layout = QVBoxLayout(self.analysis_widget)
        analysis_layout.setContentsMargins(0, 0, 0, 0)

        # Analysis header
        self.analysis_label = QLabel("")
        self.analysis_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.analysis_label.setStyleSheet("color:#1a237e; padding: 4px 0;")
        analysis_layout.addWidget(self.analysis_label)

        # Detected parameters label
        self.params_label = QLabel("")
        self.params_label.setFont(QFont("Segoe UI", 9))
        self.params_label.setStyleSheet("color:#555; padding: 2px 0;")
        self.params_label.setWordWrap(True)
        analysis_layout.addWidget(self.params_label)

        # Type distribution text
        self.type_dist_label = QLabel("")
        self.type_dist_label.setFont(QFont("Segoe UI", 10))
        self.type_dist_label.setStyleSheet("color:#1a237e; padding: 2px 0;")
        self.type_dist_label.setWordWrap(True)
        analysis_layout.addWidget(self.type_dist_label)

        # Scrollable chart area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        self.chart_container = QWidget()
        self.chart_layout = QVBoxLayout(self.chart_container)

        # Placeholder for dynamic attribute charts (will be populated at runtime)
        self.attr_charts_widget = QWidget()
        self.attr_charts_layout = QVBoxLayout(self.attr_charts_widget)
        self.attr_charts_layout.setContentsMargins(0, 0, 0, 0)
        self.chart_layout.addWidget(self.attr_charts_widget)

        # Charts: Type Distribution side by side (UNCHANGED)
        type_splitter = QSplitter(Qt.Horizontal)

        pie_group = QGroupBox("Type Distribution (Pie)")
        pie_lay = QVBoxLayout(pie_group)
        self.pie_figure = Figure(figsize=(4, 3.5), dpi=100)
        self.pie_canvas = FigureCanvas(self.pie_figure)
        self.pie_canvas.setMinimumHeight(280)
        pie_lay.addWidget(self.pie_canvas)
        type_splitter.addWidget(pie_group)

        type_bar_group = QGroupBox("Type Distribution (Bar)")
        type_bar_lay = QVBoxLayout(type_bar_group)
        self.type_bar_figure = Figure(figsize=(4, 3.5), dpi=100)
        self.type_bar_canvas = FigureCanvas(self.type_bar_figure)
        self.type_bar_canvas.setMinimumHeight(280)
        type_bar_lay.addWidget(self.type_bar_canvas)
        type_splitter.addWidget(type_bar_group)

        type_splitter.setMinimumHeight(320)
        self.chart_layout.addWidget(type_splitter)
        scroll.setWidget(self.chart_container)
        analysis_layout.addWidget(scroll, stretch=1)

        # Hide the entire analysis section by default
        self.analysis_widget.setVisible(False)
        root.addWidget(self.analysis_widget, stretch=1)

    # ── Data loading ──────────────────────────────────

    def _refresh_history(self):
        """Fetch file list only. Does NOT load stats (analysis hidden until Show)."""
        try:
            self.history_data = self.session.get_history()
        except Exception as exc:
            QMessageBox.warning(self, "Error", f"Failed to load history: {exc}")
            return
        self._fill_history(self.history_data)

    def _load_file_stats(self, file_id):
        """Fetch stats for a specific file and show the analysis section."""
        if not file_id:
            self.file_stats = None
            self.analysis_widget.setVisible(False)
            return
        try:
            self.file_stats = self.session.get_stats(file_id)
        except Exception as exc:
            QMessageBox.warning(self, "Error", f"Failed to load stats: {exc}")
            self.file_stats = None
            self.analysis_widget.setVisible(False)
            return

        # Find file name
        sel = next((h for h in self.history_data if h["id"] == file_id), None)
        name = sel["file_name"] if sel else "Selected File"
        total = self.file_stats.get("total_records", 0)
        self.analysis_label.setText(f"Analysis: {name} — {total} records")

        # Detected parameters
        numeric_columns = self.file_stats.get("numeric_columns", [])
        if numeric_columns:
            nice = ", ".join(c.replace("_", " ").title() for c in numeric_columns)
            self.params_label.setText(f"Detected Parameters: {nice}")
        else:
            self.params_label.setText("")

        # Type distribution text
        type_dist = self.file_stats.get("type_distribution", [])
        if type_dist:
            parts = [f"{t.get('type') or 'Unknown'}: {t['count']}" for t in type_dist]
            self.type_dist_label.setText(f"Type Distribution:  {',  '.join(parts)}")
        else:
            self.type_dist_label.setText("")

        # Draw dynamic attribute charts
        equipment_list = self.file_stats.get("equipment_list", [])
        self._draw_dynamic_attr_charts(equipment_list, numeric_columns)

        # Draw type distribution charts (UNCHANGED)
        self._draw_type_pie(type_dist)
        self._draw_type_bar(type_dist)
        self.analysis_widget.setVisible(True)

    # ── Dynamic per-attribute bar charts ──────────────

    def _draw_dynamic_attr_charts(self, equipment_list, numeric_columns):
        """Clear old attribute charts and create one bar chart per numeric column."""
        # Remove old canvases
        for canvas in self._attr_canvases:
            canvas.setParent(None)
            canvas.deleteLater()
        self._attr_canvases = []

        # Remove old group boxes
        while self.attr_charts_layout.count():
            item = self.attr_charts_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()

        if not equipment_list or not numeric_columns:
            return

        names = [e["name"] for e in equipment_list]
        x = np.arange(len(names))

        for idx, col in enumerate(numeric_columns):
            nice_name = col.replace("_", " ").title()
            group = QGroupBox(f"Avg {nice_name} by Equipment")
            group.setMinimumHeight(320)
            lay = QVBoxLayout(group)

            fig = Figure(figsize=(9, 3.5), dpi=100)
            ax = fig.add_subplot(111)
            color = ATTR_PALETTE[idx % len(ATTR_PALETTE)]
            values = [e.get("avg", {}).get(col, 0) for e in equipment_list]
            ax.bar(x, values, color=color, edgecolor="white", width=0.6)
            ax.set_xticks(x)
            ax.set_xticklabels(names, fontsize=8, rotation=30 if len(names) > 4 else 0,
                               ha="right" if len(names) > 4 else "center")
            ax.set_ylabel("Average Value")
            ax.set_title(f"Avg {nice_name}", fontsize=11, fontweight="bold")
            fig.tight_layout()

            canvas = FigureCanvas(fig)
            canvas.setMinimumHeight(280)
            lay.addWidget(canvas)
            self.attr_charts_layout.addWidget(group)
            self._attr_canvases.append(canvas)

    # ── Chart: Type Distribution pie (UNCHANGED) ──────

    def _draw_type_pie(self, type_dist):
        self.pie_figure.clear()
        ax = self.pie_figure.add_subplot(111)
        if not type_dist:
            ax.text(0.5, 0.5, "No data", ha="center", va="center", fontsize=14, color="#888")
        else:
            labels = [t.get("type") or "Unknown" for t in type_dist]
            sizes = [t["count"] for t in type_dist]
            clrs = [COLORS[i % len(COLORS)] for i in range(len(labels))]
            ax.pie(sizes, labels=labels, colors=clrs, autopct="%1.1f%%", startangle=140)
            ax.set_title("Type Distribution (Pie)", fontsize=11, fontweight="bold")
        self.pie_figure.tight_layout()
        self.pie_canvas.draw()

    # ── Chart: Type Distribution bar (UNCHANGED) ──────

    def _draw_type_bar(self, type_dist):
        self.type_bar_figure.clear()
        ax = self.type_bar_figure.add_subplot(111)
        if not type_dist:
            ax.text(0.5, 0.5, "No data", ha="center", va="center", fontsize=14, color="#888")
        else:
            labels = [t.get("type") or "Unknown" for t in type_dist]
            counts = [t["count"] for t in type_dist]
            clrs = [COLORS[i % len(COLORS)] for i in range(len(labels))]
            ax.bar(labels, counts, color=clrs, edgecolor="white")
            ax.set_ylabel("Count")
            ax.set_title("Type Distribution (Bar)", fontsize=11, fontweight="bold")
            ax.yaxis.get_major_locator().set_params(integer=True)
            if len(labels) > 4:
                ax.tick_params(axis="x", rotation=30)
        self.type_bar_figure.tight_layout()
        self.type_bar_canvas.draw()

    # ── History table with Show / Download PDF / Delete ──

    def _fill_history(self, history):
        self.history_table.setRowCount(len(history))
        for i, h in enumerate(history):
            self.history_table.setItem(i, 0, QTableWidgetItem(h["file_name"]))
            self.history_table.setItem(i, 1, QTableWidgetItem(str(h["rows_imported"])))
            self.history_table.setItem(i, 2, QTableWidgetItem(h["uploaded_at"]))

            upload_id = h["id"]
            is_active = self.selected_file_id == upload_id

            # Show button
            btn_show = QPushButton("Viewing ✓" if is_active else "Show")
            btn_show.setStyleSheet(
                f"background:{'#1565c0' if is_active else '#1a237e'};color:#fff;"
                "padding:4px 12px;border-radius:3px;"
            )
            btn_show.clicked.connect(lambda _, uid=upload_id: self._handle_show(uid))
            self.history_table.setCellWidget(i, 3, btn_show)

            # Download PDF button
            btn_pdf = QPushButton("Download PDF")
            btn_pdf.setStyleSheet("background:#2e7d32;color:#fff;padding:4px 12px;border-radius:3px;")
            btn_pdf.clicked.connect(lambda _, uid=upload_id: self._download_report_for(uid))
            self.history_table.setCellWidget(i, 4, btn_pdf)

            # Delete button
            btn_del = QPushButton("Delete")
            btn_del.setStyleSheet("background:#e53935;color:#fff;padding:4px 12px;border-radius:3px;")
            btn_del.clicked.connect(lambda _, uid=upload_id: self._delete_upload(uid))
            self.history_table.setCellWidget(i, 5, btn_del)

            # Highlight selected row
            if is_active:
                for col in range(3):
                    item = self.history_table.item(i, col)
                    if item:
                        item.setBackground(QColor("#e3f2fd"))

    # ── Actions ───────────────────────────────────────

    def _handle_show(self, upload_id):
        """Select a file and show its analysis."""
        self.selected_file_id = upload_id
        self._load_file_stats(upload_id)
        self._fill_history(self.history_data)  # refresh buttons

    def _delete_upload(self, upload_id):
        reply = QMessageBox.question(
            self, "Confirm Delete",
            "Delete this upload and all its data?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        try:
            self.session.delete_upload(upload_id)
            if self.selected_file_id == upload_id:
                self.selected_file_id = None
                self.file_stats = None
                self.analysis_widget.setVisible(False)
            self._refresh_history()
        except Exception as exc:
            QMessageBox.warning(self, "Delete Failed", str(exc))

    def _upload_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select CSV", "", "CSV Files (*.csv)")
        if not path:
            return
        try:
            result = self.session.upload_csv(path)
            QMessageBox.information(
                self, "Upload Successful",
                f"Imported {result['rows_imported']} rows from "
                f"{result['equipment_count']} equipment(s).",
            )
            self._refresh_history()
            # Auto-select the newly uploaded file
            new_id = result.get("upload_id")
            if new_id:
                self.selected_file_id = new_id
                self._load_file_stats(new_id)
                self._fill_history(self.history_data)
        except Exception as exc:
            QMessageBox.warning(self, "Upload Failed", str(exc))

    def _download_report_for(self, upload_id):
        """Download PDF report for a specific file."""
        path, _ = QFileDialog.getSaveFileName(self, "Save Report", "equipment_report.pdf", "PDF (*.pdf)")
        if not path:
            return
        try:
            self.session.download_report(path, upload_id)
            QMessageBox.information(self, "Report Saved", f"Report saved to:\n{path}")
        except Exception as exc:
            QMessageBox.warning(self, "Report Failed", str(exc))

    # ── Navigation ────────────────────────────────────

    def _do_logout(self):
        self.session.logout()
        self.logout_requested.emit()

    def _go_admin(self):
        self.admin_panel_requested.emit()
