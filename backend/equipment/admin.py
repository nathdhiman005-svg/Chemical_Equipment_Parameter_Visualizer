from django.contrib import admin
from .models import EquipmentData, UploadHistory


@admin.register(EquipmentData)
class EquipmentDataAdmin(admin.ModelAdmin):
    list_display = ("equipment_name", "equipment_type", "flowrate", "pressure", "temperature", "user", "timestamp")
    list_filter = ("equipment_name", "equipment_type", "user")
    search_fields = ("equipment_name", "equipment_type")


@admin.register(UploadHistory)
class UploadHistoryAdmin(admin.ModelAdmin):
    list_display = ("file_name", "rows_imported", "user", "uploaded_at")
    list_filter = ("user",)
