import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { register as apiRegister } from "../services/api";
import { useAuth } from "../context/AuthContext";

const styles = {
  container: {
    maxWidth: 420,
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

export default function RegisterPage() {
  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
    password2: "",
    company: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { signin } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (form.password !== form.password2) {
      setError("Passwords do not match.");
      return;
    }
    setLoading(true);
    try {
      const { data } = await apiRegister(form);
      signin(data.user, data.tokens);
      navigate("/dashboard");
    } catch (err) {
      const d = err.response?.data;
      const msg = d
        ? Object.values(d).flat().join(" ")
        : "Registration failed.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const f = (name, placeholder, type = "text") => (
    <input
      style={styles.input}
      type={type}
      placeholder={placeholder}
      value={form[name]}
      onChange={(e) => setForm({ ...form, [name]: e.target.value })}
      required={name !== "company"}
    />
  );

  return (
    <div style={styles.container}>
      <h2 style={styles.title}>Create Account</h2>
      {error && <p style={styles.error}>{error}</p>}
      <form onSubmit={handleSubmit}>
        {f("username", "Username")}
        {f("email", "Email", "email")}
        {f("company", "Company (optional)")}
        {f("password", "Password", "password")}
        {f("password2", "Confirm Password", "password")}
        <button style={styles.btn} disabled={loading}>
          {loading ? "Creating…" : "Register"}
        </button>
      </form>
      <p style={styles.footer}>
        Already have an account? <Link to="/login">Login</Link>
      </p>
    </div>
  );
}
