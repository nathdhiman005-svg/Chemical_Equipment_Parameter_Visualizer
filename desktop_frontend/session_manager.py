"""
SessionManager — HTTP client with JWT authentication for the desktop app.
"""

import requests

API_BASE = "http://127.0.0.1:8000/api"


class SessionManager:
    """Handles auth (login/register) and authenticated API calls via JWT."""

    def __init__(self):
        self.access_token = None
        self.refresh_token = None
        self.user = None  # dict with id, username, email, is_superuser, etc.

    # ── helpers ───────────────────────────────────────

    def _headers(self):
        h = {}
        if self.access_token:
            h["Authorization"] = f"Bearer {self.access_token}"
        return h

    def _refresh_access(self):
        """Try to refresh the access token using the refresh token."""
        if not self.refresh_token:
            raise RuntimeError("No refresh token available. Please log in again.")
        resp = requests.post(
            f"{API_BASE}/auth/token/refresh/",
            json={"refresh": self.refresh_token},
            timeout=10,
        )
        if resp.status_code != 200:
            self.access_token = None
            self.refresh_token = None
            self.user = None
            raise RuntimeError("Session expired. Please log in again.")
        data = resp.json()
        self.access_token = data["access"]
        if "refresh" in data:
            self.refresh_token = data["refresh"]

    def _request(self, method, url, **kwargs):
        """Make an authenticated request; auto-refresh on 401."""
        kwargs.setdefault("headers", {}).update(self._headers())
        kwargs.setdefault("timeout", 15)
        resp = getattr(requests, method)(url, **kwargs)
        if resp.status_code == 401 and self.refresh_token:
            self._refresh_access()
            kwargs["headers"].update(self._headers())
            resp = getattr(requests, method)(url, **kwargs)
        return resp

    @property
    def is_authenticated(self):
        return self.access_token is not None

    @property
    def is_superuser(self):
        return bool(self.user and self.user.get("is_superuser"))

    # ── Auth ──────────────────────────────────────────

    def login(self, username, password):
        resp = requests.post(
            f"{API_BASE}/auth/login/",
            json={"username": username, "password": password},
            timeout=10,
        )
        if resp.status_code != 200:
            detail = resp.json().get("detail", "Login failed.")
            raise RuntimeError(detail)
        data = resp.json()
        self.access_token = data["access"]
        self.refresh_token = data["refresh"]
        # Fetch profile for full user info
        self._fetch_profile()

    def register(self, username, email, password, password2, company=""):
        payload = {
            "username": username,
            "email": email,
            "password": password,
            "password2": password2,
            "company": company,
        }
        resp = requests.post(f"{API_BASE}/auth/register/", json=payload, timeout=10)
        if resp.status_code not in (200, 201):
            errors = resp.json()
            msg = "; ".join(
                f"{k}: {', '.join(v) if isinstance(v, list) else v}"
                for k, v in errors.items()
            )
            raise RuntimeError(msg)
        data = resp.json()
        self.access_token = data["tokens"]["access"]
        self.refresh_token = data["tokens"]["refresh"]
        self.user = data["user"]

    def _fetch_profile(self):
        resp = self._request("get", f"{API_BASE}/auth/profile/")
        if resp.status_code == 200:
            self.user = resp.json()
        else:
            self.user = {"username": "Unknown"}

    def logout(self):
        self.access_token = None
        self.refresh_token = None
        self.user = None

    # ── Equipment API calls (authenticated) ───────────

    def upload_csv(self, file_path):
        with open(file_path, "rb") as f:
            resp = self._request(
                "post",
                f"{API_BASE}/equipment/upload/",
                files={"file": f},
                timeout=30,
            )
        resp.raise_for_status()
        return resp.json()

    def get_stats(self, upload_id=None):
        params = {}
        if upload_id is not None:
            params["upload_id"] = upload_id
        resp = self._request("get", f"{API_BASE}/equipment/stats/", params=params)
        resp.raise_for_status()
        return resp.json()

    def get_history(self):
        resp = self._request("get", f"{API_BASE}/equipment/history/")
        resp.raise_for_status()
        return resp.json()

    def delete_upload(self, upload_id):
        resp = self._request("delete", f"{API_BASE}/equipment/history/{upload_id}/")
        resp.raise_for_status()

    def download_report(self, save_path, upload_id=None):
        params = {}
        if upload_id is not None:
            params["upload_id"] = upload_id
        resp = self._request("get", f"{API_BASE}/equipment/report/", params=params, timeout=30)
        resp.raise_for_status()
        with open(save_path, "wb") as f:
            f.write(resp.content)
        return save_path

    # ── Admin API calls ───────────────────────────────

    def admin_get_users(self, search=""):
        params = {"search": search} if search else {}
        resp = self._request("get", f"{API_BASE}/admin/users/", params=params)
        resp.raise_for_status()
        return resp.json()

    def admin_get_user_uploads(self, user_id):
        resp = self._request("get", f"{API_BASE}/admin/users/{user_id}/uploads/")
        resp.raise_for_status()
        return resp.json()

    def admin_delete_upload(self, upload_id):
        resp = self._request("delete", f"{API_BASE}/admin/uploads/{upload_id}/")
        resp.raise_for_status()

    def admin_download_report(self, save_path, upload_id):
        resp = self._request(
            "get", f"{API_BASE}/equipment/report/",
            params={"upload_id": upload_id}, timeout=30,
        )
        resp.raise_for_status()
        with open(save_path, "wb") as f:
            f.write(resp.content)
        return save_path
