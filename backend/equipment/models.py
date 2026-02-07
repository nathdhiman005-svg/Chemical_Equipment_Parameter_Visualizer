from django.conf import settings
from django.db import models


class EquipmentData(models.Model):
    """Stores equipment readings with specific parameter columns."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="equipment_data"
    )
    upload = models.ForeignKey(
        "UploadHistory", on_delete=models.CASCADE, null=True, blank=True, related_name="rows"
    )
    equipment_name = models.CharField(max_length=200)
    equipment_type = models.CharField(max_length=200, blank=True, default="")
    flowrate = models.FloatField(default=0.0)
    pressure = models.FloatField(default=0.0)
    temperature = models.FloatField(default=0.0)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
        verbose_name_plural = "Equipment Data"

    def __str__(self):
        return f"{self.equipment_name} ({self.equipment_type}) — F:{self.flowrate} P:{self.pressure} T:{self.temperature}"


class UploadHistory(models.Model):
    """Tracks each CSV upload event."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="uploads"
    )
    file_name = models.CharField(max_length=300)
    rows_imported = models.PositiveIntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]
        verbose_name_plural = "Upload Histories"

    def __str__(self):
        return f"{self.file_name} ({self.rows_imported} rows) by {self.user}"
