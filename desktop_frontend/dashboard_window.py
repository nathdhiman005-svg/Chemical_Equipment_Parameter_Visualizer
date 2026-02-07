"""
dashboard_window.py — Main dashboard with Matplotlib charts embedded in PyQt5.
Select-to-View workflow: Upload → File List → Analysis (hidden until a file is selected).
"""

import os
import numpy as np
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem,
    QSplitter, QGroupBox, QScrollArea, QFrame, QHeaderView,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


COLORS = ["#1a237e", "#0d47a1", "#1565c0", "#1e88e5", "#42a5f5", "#64b5f6", "#90caf9", "#bbdefb"]


class DashboardWindow(QMainWindow):
    """Dashboard: Upload → File List (Show / Download PDF / Delete) → Analysis."""

    def __init__(self, session):
        super().__init__()
        self.session = session
        self.selected_file_id = None
        self.file_stats = None
        self.history_data = []
        self.setWindowTitle("Chemical Equipment Visualizer")
        self.setMinimumSize(1100, 850)
        self._build_ui()
        self._refresh_history()

    # ── UI Construction ───────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

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
        chart_container = QWidget()
        chart_layout = QVBoxLayout(chart_container)

        # Chart 1: Equipment Averages (full width)
        equip_group = QGroupBox("Equipment Averages (Flowrate / Pressure / Temperature)")
        equip_lay = QVBoxLayout(equip_group)
        self.bar_figure = Figure(figsize=(9, 3.5), dpi=100)
        self.bar_canvas = FigureCanvas(self.bar_figure)
        equip_lay.addWidget(self.bar_canvas)
        chart_layout.addWidget(equip_group)

        # Charts 2 & 3: Type Distribution side by side
        type_splitter = QSplitter(Qt.Horizontal)

        pie_group = QGroupBox("Type Distribution (Pie)")
        pie_lay = QVBoxLayout(pie_group)
        self.pie_figure = Figure(figsize=(4, 3.5), dpi=100)
        self.pie_canvas = FigureCanvas(self.pie_figure)
        pie_lay.addWidget(self.pie_canvas)
        type_splitter.addWidget(pie_group)

        type_bar_group = QGroupBox("Type Distribution (Bar)")
        type_bar_lay = QVBoxLayout(type_bar_group)
        self.type_bar_figure = Figure(figsize=(4, 3.5), dpi=100)
        self.type_bar_canvas = FigureCanvas(self.type_bar_figure)
        type_bar_lay.addWidget(self.type_bar_canvas)
        type_splitter.addWidget(type_bar_group)

        chart_layout.addWidget(type_splitter)
        scroll.setWidget(chart_container)
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

        # Type distribution text
        type_dist = self.file_stats.get("type_distribution", [])
        if type_dist:
            parts = [f"{t.get('type') or 'Unknown'}: {t['count']}" for t in type_dist]
            self.type_dist_label.setText(f"Type Distribution:  {',  '.join(parts)}")
        else:
            self.type_dist_label.setText("")

        self._draw_equip_bar(self.file_stats.get("equipment_list", []))
        self._draw_type_pie(type_dist)
        self._draw_type_bar(type_dist)
        self.analysis_widget.setVisible(True)

    # ── Chart 1: Equipment Averages grouped bar ───────

    def _draw_equip_bar(self, equipment_list):
        self.bar_figure.clear()
        ax = self.bar_figure.add_subplot(111)
        if not equipment_list:
            ax.text(0.5, 0.5, "No data", ha="center", va="center", fontsize=14, color="#888")
        else:
            names = [e["name"] for e in equipment_list]
            x = np.arange(len(names))
            width = 0.25
            ax.bar(x - width, [e.get("avg_flowrate", 0) for e in equipment_list], width, label="Flowrate", color="#1a237e")
            ax.bar(x, [e.get("avg_pressure", 0) for e in equipment_list], width, label="Pressure", color="#1565c0")
            ax.bar(x + width, [e.get("avg_temperature", 0) for e in equipment_list], width, label="Temperature", color="#42a5f5")
            ax.set_xticks(x)
            ax.set_xticklabels(names, fontsize=8)
            ax.set_ylabel("Average Value")
            ax.set_title("Equipment Averages", fontsize=11, fontweight="bold")
            ax.legend(fontsize=8)
            if len(names) > 4:
                ax.tick_params(axis="x", rotation=30)
        self.bar_figure.tight_layout()
        self.bar_canvas.draw()

    # ── Chart 2: Type Distribution pie ────────────────

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

    # ── Chart 3: Type Distribution bar ────────────────

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
