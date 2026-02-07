import io
import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from django.http import HttpResponse
from django.contrib.auth import get_user_model
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image,
)
from reportlab.lib.styles import getSampleStyleSheet

from .models import EquipmentData, UploadHistory
from .serializers import (
    EquipmentDataSerializer,
    UploadHistorySerializer,
    CSVUploadSerializer,
)
from .services import process_csv, get_summary_stats, CSVProcessingError

CHART_COLORS = ["#1a237e", "#0d47a1", "#1565c0", "#1e88e5", "#42a5f5", "#64b5f6", "#90caf9", "#bbdefb"]


def _get_effective_user(request):
    """Return the authenticated user, or get/create a shared __desktop__ user."""
    if request.user and request.user.is_authenticated:
        return request.user
    User = get_user_model()
    user, _ = User.objects.get_or_create(username="__desktop__", defaults={"is_active": True})
    return user


def _fig_to_image(fig, width=5 * inch, height=3 * inch):
    """Render a matplotlib Figure to a ReportLab Image flowable."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return Image(buf, width=width, height=height)


ATTR_PALETTE = ["#1a237e", "#0d47a1", "#1565c0", "#2e7d32", "#e65100",
                "#6a1b9a", "#c62828", "#00695c", "#4e342e", "#37474f"]


def _make_single_attr_chart(equipment_list, attr_name, color_idx):
    """Bar chart: per-equipment average for a single numeric attribute."""
    names = [e["name"] for e in equipment_list]
    values = [e["avg"].get(attr_name, 0) for e in equipment_list]
    color = ATTR_PALETTE[color_idx % len(ATTR_PALETTE)]
    fig, ax = plt.subplots(figsize=(7, 4))
    x = np.arange(len(names))
    ax.bar(x, values, color=color, edgecolor="white", width=0.6)
    ax.set_xticks(x)
    ax.set_xticklabels(names, fontsize=8,
                       rotation=30 if len(names) > 6 else 0,
                       ha="right" if len(names) > 6 else "center")
    ax.set_ylabel("Average Value")
    nice = attr_name.replace("_", " ").title()
    ax.set_title(f"Avg {nice} by Equipment", fontsize=10, fontweight="bold")
    fig.tight_layout()
    return fig


def _make_type_pie_chart(type_distribution):
    """Pie chart: percentage distribution of equipment types."""
    labels = [t["type"] or "Unknown" for t in type_distribution]
    sizes = [t["count"] for t in type_distribution]
    clrs = [CHART_COLORS[i % len(CHART_COLORS)] for i in range(len(labels))]
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.pie(sizes, labels=labels, colors=clrs, autopct="%1.1f%%", startangle=140)
    ax.set_title("Equipment Type Distribution (Pie)", fontsize=10, fontweight="bold")
    fig.tight_layout()
    return fig


def _make_type_bar_chart(type_distribution):
    """Bar chart: absolute count of each equipment type."""
    labels = [t["type"] or "Unknown" for t in type_distribution]
    counts = [t["count"] for t in type_distribution]
    clrs = [CHART_COLORS[i % len(CHART_COLORS)] for i in range(len(labels))]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(labels, counts, color=clrs, edgecolor="white")
    ax.set_ylabel("Count")
    ax.set_title("Equipment Type Distribution (Bar)", fontsize=10, fontweight="bold")
    fig.tight_layout()
    return fig


# ──────────────────────────────────────────────
#  Upload CSV
# ──────────────────────────────────────────────
class CSVUploadView(APIView):
    """POST /api/equipment/upload/"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CSVUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            result = process_csv(serializer.validated_data["file"], _get_effective_user(request))
        except CSVProcessingError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(result, status=status.HTTP_201_CREATED)


# ──────────────────────────────────────────────
#  Summary Stats
# ──────────────────────────────────────────────
class StatsView(APIView):
    """GET /api/equipment/stats/?upload_id=<id>"""
    permission_classes = [AllowAny]

    def get(self, request):
        upload_id = request.query_params.get("upload_id")
        if upload_id is not None:
            try:
                upload_id = int(upload_id)
            except (ValueError, TypeError):
                upload_id = None
        stats = get_summary_stats(_get_effective_user(request), upload_id=upload_id)
        return Response(stats)


# ──────────────────────────────────────────────
#  Upload History (last 5)
# ──────────────────────────────────────────────
class UploadHistoryView(generics.ListAPIView):
    """GET /api/equipment/history/"""
    permission_classes = [AllowAny]
    serializer_class = UploadHistorySerializer

    def get_queryset(self):
        return UploadHistory.objects.filter(user=_get_effective_user(self.request))[:5]


class DeleteUploadView(APIView):
    """DELETE /api/equipment/history/<id>/"""
    permission_classes = [AllowAny]

    def delete(self, request, pk):
        user = _get_effective_user(request)
        try:
            upload = UploadHistory.objects.get(pk=pk, user=user)
        except UploadHistory.DoesNotExist:
            return Response({"error": "Upload not found."}, status=status.HTTP_404_NOT_FOUND)
        # Cascade deletes linked EquipmentData rows via FK
        upload.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ──────────────────────────────────────────────
#  Equipment Data List
# ──────────────────────────────────────────────
class EquipmentDataListView(generics.ListAPIView):
    """GET /api/equipment/data/"""
    permission_classes = [AllowAny]
    serializer_class = EquipmentDataSerializer

    def get_queryset(self):
        return EquipmentData.objects.filter(user=_get_effective_user(self.request))


# ──────────────────────────────────────────────
#  PDF Report
# ──────────────────────────────────────────────
class ReportView(APIView):
    """GET /api/equipment/report/?upload_id=<id>"""
    permission_classes = [AllowAny]

    def get(self, request):
        user = _get_effective_user(request)
        upload_id = request.query_params.get("upload_id")
        if upload_id is not None:
            try:
                upload_id = int(upload_id)
            except (ValueError, TypeError):
                upload_id = None
        stats = get_summary_stats(user, upload_id=upload_id)
        numeric_columns = stats.get("numeric_columns", [])

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        # Title
        elements.append(Paragraph("Chemical Equipment Parameter Report", styles["Title"]))
        elements.append(Spacer(1, 0.3 * inch))

        elements.append(
            Paragraph(f"User: {user.username}", styles["Normal"])
        )
        elements.append(
            Paragraph(f"Total Records: {stats['total_records']}", styles["Normal"])
        )
        if numeric_columns:
            elements.append(
                Paragraph(f"Detected Parameters: {', '.join(c.replace('_', ' ').title() for c in numeric_columns)}", styles["Normal"])
            )
        elements.append(Spacer(1, 0.3 * inch))

        type_dist = stats.get("type_distribution", [])

        # ── Type Distribution summary table (Equipment Type | Count) ──
        if type_dist:
            elements.append(Paragraph("Equipment Type Summary", styles["Heading2"]))
            table_data = [["Equipment Type", "Count"]]
            for t in type_dist:
                table_data.append([t["type"] or "Unknown", t["count"]])
            table = Table(table_data, hAlign="LEFT")
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4472C4")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
                    ]
                )
            )
            elements.append(table)
            elements.append(Spacer(1, 0.3 * inch))

        # ── Per-Attribute Bar Charts (one chart per numeric column) ──
        equip_list = stats.get("equipment_list", [])
        if equip_list and numeric_columns:
            for idx, col in enumerate(numeric_columns):
                nice = col.replace('_', ' ').title()
                elements.append(Paragraph(f"Avg {nice} by Equipment", styles["Heading2"]))
                fig = _make_single_attr_chart(equip_list, col, idx)
                elements.append(_fig_to_image(fig, width=5.5 * inch, height=3 * inch))
                elements.append(Spacer(1, 0.3 * inch))

        # ── Chart 2: Type Distribution Pie ──
        if type_dist:
            elements.append(Paragraph("Type Distribution — Pie Chart", styles["Heading2"]))
            fig = _make_type_pie_chart(type_dist)
            elements.append(_fig_to_image(fig, width=4 * inch, height=3 * inch))
            elements.append(Spacer(1, 0.3 * inch))

        # ── Chart 3: Type Distribution Bar ──
        if type_dist:
            elements.append(Paragraph("Type Distribution — Bar Chart", styles["Heading2"]))
            fig = _make_type_bar_chart(type_dist)
            elements.append(_fig_to_image(fig, width=5 * inch, height=3 * inch))

        doc.build(elements)
        buffer.seek(0)

        response = HttpResponse(buffer, content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="equipment_report.pdf"'
        return response
