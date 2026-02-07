from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    password2 = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ("id", "username", "email", "password", "password2", "company", "role")

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "company", "role", "date_joined", "is_superuser")
        read_only_fields = fields


class AdminUserSerializer(serializers.ModelSerializer):
    """Serializer used by admin endpoints to list all users."""

    class Meta:
        model = User
        fields = ("id", "username", "email", "date_joined", "company", "role", "is_superuser", "is_active")
        read_only_fields = fields
