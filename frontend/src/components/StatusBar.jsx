import { useState, useEffect } from "react";

const SERVER_HOST = import.meta.env.VITE_MODBUS_HOST || window.location.hostname;
const MODBUS_PORT = import.meta.env.VITE_MODBUS_PORT || "502";
const API_BASE    = import.meta.env.VITE_API_URL || `http://${window.location.hostname}:8000`;

export function StatusBar({ wsStatus, registerCount, onReload, onUpload }) {
  const [copied, setCopied]       = useState(false);
  const [reloading, setReloading] = useState(false);
  const [unitId, setUnitId]       = useState(1);
  const [editingUid, setEditingUid] = useState(false);
  const [draftUid, setDraftUid]   = useState("1");
  const [uidError, setUidError]   = useState(null);
  const [uidSaving, setUidSaving] = useState(false);

  const address = `${SERVER_HOST}:${MODBUS_PORT}`;

  // Fetch current unit ID on mount
  useEffect(() => {
    fetch(`${API_BASE}/config/unit-id`)
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d) { setUnitId(d.unit_id); setDraftUid(String(d.unit_id)); } })
      .catch(() => {});
  }, []);

  const copy = () => {
    navigator.clipboard.writeText(address);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const handleReload = async () => {
    setReloading(true);
    try { await onReload(); } finally { setReloading(false); }
  };

  const handleFile = (e) => {
    const file = e.target.files[0];
    if (file) onUpload(file);
    e.target.value = "";
  };

  const saveUnitId = async () => {
    const val = parseInt(draftUid);
    if (isNaN(val) || val < 1 || val > 247) {
      setUidError("1–247");
      return;
    }
    setUidSaving(true);
    try {
      const res = await fetch(`${API_BASE}/config/unit-id`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ unit_id: val }),
      });
      if (!res.ok) throw new Error();
      setUnitId(val);
      setEditingUid(false);
      setUidError(null);
    } catch {
      setUidError("Failed");
    } finally {
      setUidSaving(false);
    }
  };

  const dot   = wsStatus === "open" ? "#22c55e" : wsStatus === "connecting" ? "#f59e0b" : "#ef4444";
  const label = wsStatus === "open" ? "Live" : wsStatus === "connecting" ? "Connecting…" : "Disconnected";

  const inputStyle = {
    background: "#0D0F14", border: "1px solid #2a2d38", borderRadius: 3,
    color: "#fff", padding: "0.15rem 0.4rem", fontSize: "0.72rem",
    fontFamily: "inherit", width: 48,
  };

  const btnStyle = (color) => ({
    background: "none", border: `1px solid ${color}44`,
    borderRadius: 3, color, padding: "0.15rem 0.45rem",
    cursor: "pointer", fontSize: "0.66rem", fontFamily: "inherit",
  });

  return (
    <div style={{
      display: "flex", alignItems: "center", gap: "1.25rem",
      padding: "0.6rem 1.25rem",
      background: "#13151C",
      borderBottom: "1px solid #1E2028",
      fontSize: "0.75rem",
      flexWrap: "wrap",
    }}>
      {/* WS status */}
      <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
        <span style={{
          width: 8, height: 8, borderRadius: "50%", background: dot,
          boxShadow: `0 0 6px ${dot}`, display: "inline-block",
          animation: wsStatus === "open" ? "pulse 2s infinite" : "none"
        }} />
        <span style={{ color: "#aaa" }}>{label}</span>
      </div>

      {/* Modbus address */}
      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
        <span style={{ color: "#555" }}>Modbus TCP</span>
        <code style={{
          background: "#0D0F14", border: "1px solid #1E2028",
          padding: "0.15rem 0.5rem", borderRadius: 3, color: "#00D4AA", fontSize: "0.72rem",
        }}>{address}</code>
        <button onClick={copy} style={{
          background: "none", border: "1px solid #1E2028", borderRadius: 3,
          color: copied ? "#22c55e" : "#666", padding: "0.15rem 0.5rem",
          cursor: "pointer", fontSize: "0.68rem"
        }}>{copied ? "✓ Copied" : "Copy"}</button>
      </div>

      {/* Unit ID */}
      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
        <span style={{ color: "#555" }}>Unit ID</span>
        {editingUid ? (
          <>
            <input
              value={draftUid}
              onChange={e => setDraftUid(e.target.value)}
              onKeyDown={e => { if (e.key === "Enter") saveUnitId(); if (e.key === "Escape") { setEditingUid(false); setUidError(null); } }}
              style={inputStyle}
              autoFocus
            />
            <button onClick={saveUnitId} disabled={uidSaving} style={btnStyle("#00D4AA")}>
              {uidSaving ? "…" : "✓"}
            </button>
            <button onClick={() => { setEditingUid(false); setUidError(null); setDraftUid(String(unitId)); }} style={btnStyle("#555")}>✕</button>
            {uidError && <span style={{ color: "#ef4444", fontSize: "0.65rem" }}>{uidError}</span>}
          </>
        ) : (
          <code
            onClick={() => { setDraftUid(String(unitId)); setEditingUid(true); }}
            title="Click to change unit ID"
            style={{
              background: "#0D0F14", border: "1px solid #1E2028",
              padding: "0.15rem 0.5rem", borderRadius: 3, color: "#a78bfa",
              fontSize: "0.72rem", cursor: "pointer",
              borderBottom: "1px dashed #a78bfa55",
            }}
          >{unitId}</code>
        )}
      </div>

      {/* Register count */}
      <span style={{ color: "#555" }}>
        <span style={{ color: "#aaa" }}>{registerCount}</span> registers
      </span>

      <div style={{ marginLeft: "auto", display: "flex", gap: "0.5rem" }}>
        <label style={{
          background: "#1E2028", border: "1px solid #2a2d38", borderRadius: 4,
          color: "#aaa", padding: "0.3rem 0.75rem", cursor: "pointer", fontSize: "0.72rem"
        }}>
          ⬆ Upload CSV
          <input type="file" accept=".csv" onChange={handleFile} style={{ display: "none" }} />
        </label>
        <button onClick={handleReload} disabled={reloading} style={{
          background: "#1E2028", border: "1px solid #2a2d38", borderRadius: 4,
          color: reloading ? "#555" : "#aaa", padding: "0.3rem 0.75rem",
          cursor: "pointer", fontSize: "0.72rem"
        }}>{reloading ? "Reloading…" : "↺ Reload CSV"}</button>
      </div>

      <style>{`@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }`}</style>
    </div>
  );
}
