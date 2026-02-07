"""Core URL configuration."""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from users.views import AdminUserListView, AdminUserUploadsView, AdminDeleteUploadView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("users.urls")),
    path("api/equipment/", include("equipment.urls")),
    # Admin API
    path("api/admin/users/", AdminUserListView.as_view(), name="admin-user-list"),
    path("api/admin/users/<int:user_id>/uploads/", AdminUserUploadsView.as_view(), name="admin-user-uploads"),
    path("api/admin/uploads/<int:pk>/", AdminDeleteUploadView.as_view(), name="admin-delete-upload"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
