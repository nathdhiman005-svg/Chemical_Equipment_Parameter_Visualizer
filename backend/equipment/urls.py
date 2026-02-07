from django.urls import path
from .views import (
    CSVUploadView,
    StatsView,
    UploadHistoryView,
    DeleteUploadView,
    EquipmentDataListView,
    ReportView,
)

urlpatterns = [
    path("upload/", CSVUploadView.as_view(), name="equipment-upload"),
    path("stats/", StatsView.as_view(), name="equipment-stats"),
    path("history/", UploadHistoryView.as_view(), name="equipment-history"),
    path("history/<int:pk>/", DeleteUploadView.as_view(), name="equipment-delete"),
    path("data/", EquipmentDataListView.as_view(), name="equipment-data"),
    path("report/", ReportView.as_view(), name="equipment-report"),
]
