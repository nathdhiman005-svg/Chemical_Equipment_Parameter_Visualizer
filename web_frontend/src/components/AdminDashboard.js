import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { adminGetUsers } from "../services/api";

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
  subtitle: { color: "#555", fontSize: 14, marginBottom: 20 },
  searchWrap: { marginBottom: 16 },
  searchInput: {
    width: "100%",
    padding: "10px 14px",
    border: "1px solid #ccc",
    borderRadius: 4,
    fontSize: 14,
    boxSizing: "border-box",
  },
  table: { width: "100%", borderCollapse: "collapse", fontSize: 13, marginTop: 10 },
  th: {
    textAlign: "left",
    borderBottom: "2px solid #1a237e",
    padding: "8px 10px",
    color: "#1a237e",
    fontWeight: 600,
  },
  td: { borderBottom: "1px solid #eee", padding: "8px 10px" },
  row: { cursor: "pointer", transition: "background 0.15s" },
  badge: {
    display: "inline-block",
    padding: "2px 8px",
    borderRadius: 10,
    fontSize: 11,
    fontWeight: 600,
    color: "#fff",
    background: "#e53935",
    marginLeft: 8,
  },
  empty: { textAlign: "center", padding: 32, color: "#999" },
  error: { color: "#e53935", textAlign: "center", marginTop: 12, fontSize: 13 },
};

export default function AdminDashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [users, setUsers] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchUsers = useCallback(async (query) => {
    setLoading(true);
    setError("");
    try {
      const { data } = await adminGetUsers(query);
      setUsers(data);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load users.");
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial load
  useEffect(() => {
    fetchUsers("");
  }, [fetchUsers]);

  // Real-time search with debounce
  useEffect(() => {
    const timer = setTimeout(() => {
      fetchUsers(search);
    }, 300);
    return () => clearTimeout(timer);
  }, [search, fetchUsers]);

  const handleRowClick = (userId) => {
    navigate(`/admin-dashboard/user/${userId}`);
  };

  const formatDate = (iso) => {
    if (!iso) return "—";
    return new Date(iso).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  return (
    <div style={s.page}>
      <div style={s.card}>
        <h2 style={s.heading}>Admin Panel: {user?.username}</h2>
        <p style={s.subtitle}>Manage all registered users and their data uploads</p>

        {/* Search Bar */}
        <div style={s.searchWrap}>
          <input
            style={s.searchInput}
            type="text"
            placeholder="Search by username or email…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        {error && <p style={s.error}>{error}</p>}

        {loading ? (
          <p style={s.empty}>Loading users…</p>
        ) : users.length === 0 ? (
          <p style={s.empty}>No users found.</p>
        ) : (
          <table style={s.table}>
            <thead>
              <tr>
                <th style={s.th}>ID</th>
                <th style={s.th}>Username</th>
                <th style={s.th}>Email</th>
                <th style={s.th}>Registration Date</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr
                  key={u.id}
                  style={s.row}
                  onClick={() => handleRowClick(u.id)}
                  onMouseEnter={(e) => (e.currentTarget.style.background = "#f5f5ff")}
                  onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                >
                  <td style={s.td}>{u.id}</td>
                  <td style={s.td}>
                    {u.username}
                    {u.is_superuser && <span style={s.badge}>ADMIN</span>}
                  </td>
                  <td style={s.td}>{u.email || "—"}</td>
                  <td style={s.td}>{formatDate(u.date_joined)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
