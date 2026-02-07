from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import RegisterSerializer, UserSerializer, AdminUserSerializer
from equipment.serializers import UploadHistorySerializer
from equipment.models import UploadHistory


User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """POST /api/auth/register/  — Public registration endpoint."""

    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
            },
            status=status.HTTP_201_CREATED,
        )


class ProfileView(APIView):
    """GET /api/auth/profile/  — Returns the authenticated user's profile."""

    def get(self, request):
        return Response(UserSerializer(request.user).data)


# ──────────────────────────────────────────────
#  Admin-only endpoints
# ──────────────────────────────────────────────

class AdminUserListView(generics.ListAPIView):
    """GET /api/admin/users/?search=<term>
    Returns all users. Supports ?search= for username/email filtering.
    Superuser only.
    """
    serializer_class = AdminUserSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        qs = User.objects.all().order_by("-date_joined")
        search = self.request.query_params.get("search", "").strip()
        if search:
            qs = qs.filter(Q(username__icontains=search) | Q(email__icontains=search))
        return qs


class AdminUserUploadsView(APIView):
    """GET /api/admin/users/<user_id>/uploads/
    Returns ALL uploads for a given user (no limit).
    Superuser only.
    """
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, user_id):
        try:
            target_user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        uploads = UploadHistory.objects.filter(user=target_user)  # no limit — full history
        serializer = UploadHistorySerializer(uploads, many=True)

        user_info = AdminUserSerializer(target_user).data
        return Response({"user": user_info, "uploads": serializer.data})


class AdminDeleteUploadView(APIView):
    """DELETE /api/admin/uploads/<id>/
    Allows superuser to delete any upload regardless of owner.
    """
    permission_classes = [permissions.IsAdminUser]

    def delete(self, request, pk):
        try:
            upload = UploadHistory.objects.get(pk=pk)
        except UploadHistory.DoesNotExist:
            return Response({"error": "Upload not found."}, status=status.HTTP_404_NOT_FOUND)
        upload.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
