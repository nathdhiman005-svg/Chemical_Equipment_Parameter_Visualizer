import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const styles = {
  nav: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "12px 24px",
    background: "linear-gradient(135deg, #1a237e 0%, #0d47a1 100%)",
    color: "#fff",
    boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
  },
  brand: { fontSize: 18, fontWeight: 700, textDecoration: "none", color: "#fff" },
  links: { display: "flex", gap: 16, alignItems: "center" },
  link: { color: "#bbdefb", textDecoration: "none", fontSize: 14 },
  btn: {
    background: "#e53935",
    border: "none",
    color: "#fff",
    padding: "6px 14px",
    borderRadius: 4,
    cursor: "pointer",
    fontSize: 13,
  },
};

export default function Navbar() {
  const { isAuthenticated, user, signout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    signout();
    navigate("/login");
  };

  return (
    <nav style={styles.nav}>
      <Link to="/" style={styles.brand}>
        ⚗️ Chemical Visualizer
      </Link>
      <div style={styles.links}>
        {isAuthenticated ? (
          <>
            <Link to="/dashboard" style={styles.link}>Dashboard</Link>
            <span style={{ fontSize: 13 }}>Hi, {user?.username}</span>
            <button onClick={handleLogout} style={styles.btn}>Logout</button>
          </>
        ) : (
          <>
            <Link to="/login" style={styles.link}>Login</Link>
            <Link to="/register" style={styles.link}>Register</Link>
          </>
        )}
      </div>
    </nav>
  );
}
