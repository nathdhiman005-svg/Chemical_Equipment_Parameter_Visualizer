import React, { useState, useEffect, useCallback, useRef } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Tooltip,
  Legend,
  Title,
} from "chart.js";
import { Bar, Pie } from "react-chartjs-2";
import { uploadCSV, getStats, getHistory, deleteUpload, downloadReport } from "../services/api";

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, Tooltip, Legend, Title);

const COLORS = ["#1a237e", "#0d47a1", "#1565c0", "#1e88e5", "#42a5f5", "#64b5f6", "#90caf9", "#bbdefb"];

const s = {
  page: { maxWidth: 960, margin: "24px auto", padding: "0 16px" },
  card: {
    background: "#fff",
    borderRadius: 8,
    padding: 20,
    marginBottom: 20,
    boxShadow: "0 1px 6px rgba(0,0,0,0.07)",
  },
  grid: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 },
  heading: { color: "#1a237e", marginBottom: 12 },
  input: { marginRight: 12 },
  btn: {
    padding: "8px 18px",
    background: "#1a237e",
    color: "#fff",
    border: "none",
    borderRadius: 4,
    cursor: "pointer",
    fontSize: 14,
    marginRight: 8,
  },
  btnSmall: {
    padding: "4px 12px",
    border: "none",
    borderRadius: 4,
    cursor: "pointer",
    fontSize: 12,
    marginRight: 4,
  },
  msg: { padding: 8, marginTop: 8, borderRadius: 4, fontSize: 13 },
  table: { width: "100%", borderCollapse: "collapse", fontSize: 13, marginTop: 10 },
  th: { textAlign: "left", borderBottom: "2px solid #1a237e", padding: "6px 8px", color: "#1a237e" },
  td: { borderBottom: "1px solid #eee", padding: "6px 8px" },
};

export default function Dashboard() {
  const [file, setFile] = useState(null);
  const [uploadMsg, setUploadMsg] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [history, setHistory] = useState([]);
  const [selectedFileId, setSelectedFileId] = useState(null);
  const [fileStats, setFileStats] = useState(null);
  const fileInputRef = useRef(null);

  /* ── Load history list only ── */
  const refreshHistory = useCallback(async () => {
    try {
      const { data } = await getHistory();
      setHistory(data);
    } catch {
      /* interceptor */
    }
  }, []);

  /* ── Load stats for a specific file ── */
  const loadFileStats = useCallback(async (id) => {
    if (!id) {
      setFileStats(null);
      return;
    }
    try {
      const { data } = await getStats(id);
      setFileStats(data);
    } catch {
      setFileStats(null);
    }
  }, []);

  useEffect(() => {
    refreshHistory();
  }, [refreshHistory]);

  /* ── Upload ── */
  const handleUpload = async () => {
    if (!file || uploading) return;
    setUploadMsg(null);
    setUploading(true);
    try {
      const { data } = await uploadCSV(file);
      setUploadMsg({
        ok: true,
        text: `Imported ${data.rows_imported} rows from ${data.equipment_count} equipment(s).`,
      });
      setFile(null);
      // Reset the file input so the same file can be re-selected
      if (fileInputRef.current) fileInputRef.current.value = "";
      await refreshHistory();
      // Auto-select the newly uploaded file
      setSelectedFileId(data.upload_id);
      loadFileStats(data.upload_id);
    } catch (err) {
      setUploadMsg({ ok: false, text: err.response?.data?.error || "Upload failed." });
    } finally {
      setUploading(false);
    }
  };

  /* ── Show (select) a file ── */
  const handleShow = (id) => {
    setSelectedFileId(id);
    loadFileStats(id);
  };

  /* ── Download PDF for a specific file ── */
  const handleDownloadPDF = async (id) => {
    try {
      const { data } = await downloadReport(id);
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

  /* ── Delete a file ── */
  const handleDelete = async (id) => {
    if (!window.confirm("Delete this upload and all its data?")) return;
    try {
      await deleteUpload(id);
      if (selectedFileId === id) {
        setSelectedFileId(null);
        setFileStats(null);
      }
      refreshHistory();
    } catch {
      alert("Failed to delete upload.");
    }
  };

  /* ── Chart data builders (only from fileStats) ── */
  const barData = fileStats?.equipment_list?.length
    ? {
        labels: fileStats.equipment_list.map((e) => e.name),
        datasets: [
          { label: "Avg Flowrate", data: fileStats.equipment_list.map((e) => e.avg_flowrate), backgroundColor: "#1a237e", borderRadius: 4 },
          { label: "Avg Pressure", data: fileStats.equipment_list.map((e) => e.avg_pressure), backgroundColor: "#1565c0", borderRadius: 4 },
          { label: "Avg Temperature", data: fileStats.equipment_list.map((e) => e.avg_temperature), backgroundColor: "#42a5f5", borderRadius: 4 },
        ],
      }
    : null;

  const typeDist = fileStats?.type_distribution || [];
  const typePieData = typeDist.length
    ? { labels: typeDist.map((t) => t.type || "Unknown"), datasets: [{ data: typeDist.map((t) => t.count), backgroundColor: typeDist.map((_, i) => COLORS[i % COLORS.length]) }] }
    : null;
  const typeBarData = typeDist.length
    ? { labels: typeDist.map((t) => t.type || "Unknown"), datasets: [{ label: "Count", data: typeDist.map((t) => t.count), backgroundColor: typeDist.map((_, i) => COLORS[i % COLORS.length]), borderRadius: 4 }] }
    : null;

  const selectedFile = selectedFileId ? history.find((h) => h.id === selectedFileId) : null;

  return (
    <div style={s.page}>
      {/* ═══ 1. UPLOAD SECTION (top) ═══ */}
      <div style={s.card}>
        <h3 style={s.heading}>Upload CSV</h3>
        <input ref={fileInputRef} type="file" accept=".csv" style={s.input} onChange={(e) => setFile(e.target.files[0] || null)} />
        <button style={s.btn} onClick={handleUpload} disabled={!file || uploading}>
          {uploading ? "Uploading…" : "Upload"}
        </button>
        {uploadMsg && (
          <div style={{ ...s.msg, background: uploadMsg.ok ? "#e8f5e9" : "#ffebee", color: uploadMsg.ok ? "#2e7d32" : "#c62828" }}>
            {uploadMsg.text}
          </div>
        )}
      </div>

      {/* ═══ 2. UPLOADED FILES LIST (middle) ═══ */}
      {history.length > 0 && (
        <div style={s.card}>
          <h3 style={s.heading}>Uploaded Files</h3>
          <p style={{ fontSize: 13, color: "#666", margin: "0 0 8px" }}>
            Click <b>Show</b> on a file to view its analysis below.
            <span style={{ display: "block", marginTop: 4, color: "#e65100", fontStyle: "italic" }}>
              Only the 5 most recent uploads are kept. Older uploads are automatically deleted.
            </span>
          </p>
          <table style={s.table}>
            <thead>
              <tr>
                <th style={s.th}>File</th>
                <th style={s.th}>Rows</th>
                <th style={s.th}>Date</th>
                <th style={s.th}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {history.map((h) => {
                const isActive = selectedFileId === h.id;
                return (
                  <tr key={h.id} style={isActive ? { background: "#e3f2fd" } : {}}>
                    <td style={s.td}>{h.file_name}</td>
                    <td style={s.td}>{h.rows_imported}</td>
                    <td style={s.td}>{new Date(h.uploaded_at).toLocaleString()}</td>
                    <td style={s.td}>
                      <button
                        style={{ ...s.btnSmall, background: isActive ? "#1565c0" : "#1a237e", color: "#fff" }}
                        onClick={() => handleShow(h.id)}
                      >
                        {isActive ? "Viewing ✓" : "Show"}
                      </button>
                      <button
                        style={{ ...s.btnSmall, background: "#2e7d32", color: "#fff" }}
                        onClick={() => handleDownloadPDF(h.id)}
                      >
                        Download PDF
                      </button>
                      <button
                        style={{ ...s.btnSmall, background: "#e53935", color: "#fff" }}
                        onClick={() => handleDelete(h.id)}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* ═══ 3. FILE ANALYSIS (bottom — hidden until a file is selected) ═══ */}
      {selectedFileId && fileStats && (
        <>
          {/* Overview for the selected file */}
          <div style={s.card}>
            <h3 style={s.heading}>
              Analysis: {selectedFile?.file_name || "Selected File"} — {fileStats.total_records} records
            </h3>
            {typeDist.length > 0 && (
              <div style={{ marginTop: 8 }}>
                <strong style={{ color: "#1a237e", fontSize: 14 }}>Type Distribution: </strong>
                <span style={{ fontSize: 14 }}>{typeDist.map((t) => `${t.type || "Unknown"}: ${t.count}`).join(", ")}</span>
              </div>
            )}
          </div>

          {/* Equipment Averages Chart */}
          {barData && (
            <div style={s.card}>
              <h4 style={s.heading}>Equipment Averages (Flowrate / Pressure / Temperature)</h4>
              <Bar data={barData} options={{ responsive: true, plugins: { legend: { position: "top" }, title: { display: false } }, scales: { y: { beginAtZero: true } } }} />
            </div>
          )}

          {/* Type Distribution Charts */}
          {typePieData && typeBarData && (
            <div style={s.grid}>
              <div style={s.card}>
                <h4 style={s.heading}>Type Distribution (Pie)</h4>
                <Pie data={typePieData} options={{ responsive: true, plugins: { legend: { position: "bottom" } } }} />
              </div>
              <div style={s.card}>
                <h4 style={s.heading}>Type Distribution (Bar)</h4>
                <Bar data={typeBarData} options={{ responsive: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } } }} />
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
