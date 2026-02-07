import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { login as apiLogin } from "../services/api";
import { useAuth } from "../context/AuthContext";

const styles = {
  container: {
    maxWidth: 400,
    margin: "60px auto",
    padding: 32,
    background: "#fff",
    borderRadius: 8,
    boxShadow: "0 2px 12px rgba(0,0,0,0.08)",
  },
  title: { textAlign: "center", marginBottom: 24, color: "#1a237e" },
  input: {
    width: "100%",
    padding: "10px 12px",
    marginBottom: 14,
    border: "1px solid #ccc",
    borderRadius: 4,
    fontSize: 14,
  },
  btn: {
    width: "100%",
    padding: 12,
    background: "#1a237e",
    color: "#fff",
    border: "none",
    borderRadius: 4,
    fontSize: 15,
    cursor: "pointer",
  },
  error: { color: "#e53935", textAlign: "center", marginBottom: 12, fontSize: 13 },
  footer: { textAlign: "center", marginTop: 16, fontSize: 13 },
};

export default function LoginPage() {
  const [form, setForm] = useState({ username: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { signin } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const { data } = await apiLogin(form);
      // SimpleJWT returns { access, refresh } on login
      signin({ username: form.username }, { access: data.access, refresh: data.refresh });
      navigate("/dashboard");
    } catch (err) {
      setError(err.response?.data?.detail || "Login failed. Check credentials.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <h2 style={styles.title}>Sign In</h2>
      {error && <p style={styles.error}>{error}</p>}
      <form onSubmit={handleSubmit}>
        <input
          style={styles.input}
          placeholder="Username"
          value={form.username}
          onChange={(e) => setForm({ ...form, username: e.target.value })}
          required
        />
        <input
          style={styles.input}
          type="password"
          placeholder="Password"
          value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })}
          required
        />
        <button style={styles.btn} disabled={loading}>
          {loading ? "Signing in…" : "Login"}
        </button>
      </form>
      <p style={styles.footer}>
        Don't have an account? <Link to="/register">Register</Link>
      </p>
    </div>
  );
}
