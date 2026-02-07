import React, { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { adminGetUserUploads, adminDeleteUpload, adminDownloadReport } from "../services/api";

const s = {
  page: { maxWidth: 960, margin: "24px auto", padding: "0 16px" },
  card: {
    background: "#fff",
    borderRadius: 8,
    padding: 20,
    marginBottom: 20,
    boxShadow: "0 1px 6px rgba(0,0,0,0.07)",
  },
  heading: { color: "#1a237e", marginBottom: 4 },
  back: {
    display: "inline-block",
    marginBottom: 16,
    color: "#1a237e",
    cursor: "pointer",
    fontSize: 14,
    textDecoration: "none",
    border: "none",
    background: "none",
    padding: 0,
  },
  infoGrid: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr 1fr",
    gap: 16,
    marginBottom: 20,
  },
  infoItem: {
    background: "#f5f5ff",
    borderRadius: 6,
    padding: 14,
  },
  infoLabel: { fontSize: 11, color: "#888", textTransform: "uppercase", marginBottom: 4 },
  infoValue: { fontSize: 15, fontWeight: 600, color: "#1a237e" },
  sectionTitle: { color: "#1a237e", marginBottom: 12, fontSize: 16 },
  table: { width: "100%", borderCollapse: "collapse", fontSize: 13, marginTop: 10 },
  th: {
    textAlign: "left",
    borderBottom: "2px solid #1a237e",
    padding: "8px 10px",
    color: "#1a237e",
    fontWeight: 600,
  },
  td: { borderBottom: "1px solid #eee", padding: "8px 10px" },
  btn: {
    padding: "4px 12px",
    border: "none",
    borderRadius: 4,
    cursor: "pointer",
    fontSize: 12,
    marginRight: 4,
    color: "#fff",
  },
  btnDownload: { background: "#1565c0" },
  btnDelete: { background: "#e53935" },
  empty: { textAlign: "center", padding: 32, color: "#999" },
  error: { color: "#e53935", textAlign: "center", marginTop: 12, fontSize: 13 },
  passwordField: {
    fontFamily: "monospace",
    color: "#888",
    fontSize: 12,
    letterSpacing: 2,
  },
};

export default function AdminUserDetail() {
  const { userId } = useParams();
  const navigate = useNavigate();
  const [userInfo, setUserInfo] = useState(null);
  const [uploads, setUploads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const { data } = await adminGetUserUploads(userId);
      setUserInfo(data.user);
      setUploads(data.uploads);
    } catch (err) {
      setError(err.response?.data?.error || err.response?.data?.detail || "Failed to load user data.");
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleDelete = async (uploadId) => {
    if (!window.confirm("Delete this upload and all its data?")) return;
    try {
      await adminDeleteUpload(uploadId);
      setUploads((prev) => prev.filter((u) => u.id !== uploadId));
    } catch {
      alert("Failed to delete upload.");
    }
  };

  const handleDownload = async (uploadId) => {
    try {
      const { data } = await adminDownloadReport(uploadId);
      const url = URL.createObjectURL(new Blob([data], { type: "application/pdf" }));
      const a = document.createElement("a");
      a.href = url;
      a.download = "equipment_report.pdf";
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      alert("Failed to generate report.");
    }
  };

  const formatDate = (iso) => {
    if (!iso) return "—";
    return new Date(iso).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  if (loading) {
    return (
      <div style={s.page}>
        <div style={s.card}>
          <p style={s.empty}>Loading user details…</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={s.page}>
        <div style={s.card}>
          <button style={s.back} onClick={() => navigate("/admin-dashboard")}>
            ← Back to Admin Panel
          </button>
          <p style={s.error}>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div style={s.page}>
      {/* Back link */}
      <button style={s.back} onClick={() => navigate("/admin-dashboard")}>
        ← Back to Admin Panel
      </button>

      {/* User Info Card */}
      <div style={s.card}>
        <h2 style={s.heading}>User Detail: {userInfo?.username}</h2>
        <div style={s.infoGrid}>
          <div style={s.infoItem}>
            <div style={s.infoLabel}>Username</div>
            <div style={s.infoValue}>{userInfo?.username}</div>
          </div>
          <div style={s.infoItem}>
            <div style={s.infoLabel}>Email</div>
            <div style={s.infoValue}>{userInfo?.email || "—"}</div>
          </div>
          <div style={s.infoItem}>
            <div style={s.infoLabel}>Registration Date</div>
            <div style={s.infoValue}>{formatDate(userInfo?.date_joined)}</div>
          </div>
          <div style={s.infoItem}>
            <div style={s.infoLabel}>Company</div>
            <div style={s.infoValue}>{userInfo?.company || "—"}</div>
          </div>
          <div style={s.infoItem}>
            <div style={s.infoLabel}>Role</div>
            <div style={s.infoValue}>{userInfo?.role || "—"}</div>
          </div>
          <div style={s.infoItem}>
            <div style={s.infoLabel}>Password</div>
            <div style={s.passwordField}>••••••••••• (hashed)</div>
          </div>
        </div>
      </div>

      {/* Full Upload History */}
      <div style={s.card}>
        <h3 style={s.sectionTitle}>
          Complete Upload History ({uploads.length} file{uploads.length !== 1 ? "s" : ""})
        </h3>

        {uploads.length === 0 ? (
          <p style={s.empty}>This user has not uploaded any files.</p>
        ) : (
          <table style={s.table}>
            <thead>
              <tr>
                <th style={s.th}>ID</th>
                <th style={s.th}>File Name</th>
                <th style={s.th}>Rows Imported</th>
                <th style={s.th}>Uploaded At</th>
                <th style={s.th}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {uploads.map((upload) => (
                <tr key={upload.id}>
                  <td style={s.td}>{upload.id}</td>
                  <td style={s.td}>{upload.file_name}</td>
                  <td style={s.td}>{upload.rows_imported}</td>
                  <td style={s.td}>{formatDate(upload.uploaded_at)}</td>
                  <td style={s.td}>
                    <button
                      style={{ ...s.btn, ...s.btnDownload }}
                      onClick={() => handleDownload(upload.id)}
                    >
                      Download
                    </button>
                    <button
                      style={{ ...s.btn, ...s.btnDelete }}
                      onClick={() => handleDelete(upload.id)}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
