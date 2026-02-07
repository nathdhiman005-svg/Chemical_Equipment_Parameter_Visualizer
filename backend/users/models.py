from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """Extended user model for the Chemical Visualizer platform."""

    company = models.CharField(max_length=200, blank=True, default="")
    role = models.CharField(
        max_length=20,
        choices=[("engineer", "Engineer"), ("manager", "Manager"), ("admin", "Admin")],
        default="engineer",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_joined"]

    def __str__(self):
        return f"{self.username} ({self.role})"
