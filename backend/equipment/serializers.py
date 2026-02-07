from rest_framework import serializers
from .models import EquipmentData, UploadHistory


class EquipmentDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentData
        fields = (
            "id", "equipment_name", "equipment_type",
            "flowrate", "pressure", "temperature",
            "numeric_attributes", "timestamp",
        )
        read_only_fields = ("id", "timestamp")


class UploadHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadHistory
        fields = ("id", "file_name", "rows_imported", "numeric_columns", "uploaded_at")
        read_only_fields = fields


class CSVUploadSerializer(serializers.Serializer):
    file = serializers.FileField()

    def validate_file(self, value):
        if not value.name.lower().endswith(".csv"):
            raise serializers.ValidationError("Only CSV files are accepted.")
        if value.size > 10 * 1024 * 1024:  # 10 MB limit
            raise serializers.ValidationError("File size must be under 10 MB.")
        return value
