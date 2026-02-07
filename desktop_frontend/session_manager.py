"""
SessionManager — Lightweight HTTP client for the desktop app.
No authentication required; uses the API's anonymous/desktop mode.
"""

import requests

API_BASE = "http://127.0.0.1:8000/api"


class SessionManager:
    """Makes plain HTTP calls to the backend API (no JWT)."""

    def __init__(self):
        self.username = "Desktop"

    # ── API calls ─────────────────────────────────────

    def upload_csv(self, file_path):
        with open(file_path, "rb") as f:
            resp = requests.post(
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
        resp = requests.get(f"{API_BASE}/equipment/stats/", params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def get_history(self):
        resp = requests.get(f"{API_BASE}/equipment/history/", timeout=15)
        resp.raise_for_status()
        return resp.json()

    def delete_upload(self, upload_id):
        resp = requests.delete(f"{API_BASE}/equipment/history/{upload_id}/", timeout=15)
        resp.raise_for_status()

    def download_report(self, save_path, upload_id=None):
        params = {}
        if upload_id is not None:
            params["upload_id"] = upload_id
        resp = requests.get(f"{API_BASE}/equipment/report/", params=params, timeout=30)
        resp.raise_for_status()
        with open(save_path, "wb") as f:
            f.write(resp.content)
        return save_path
