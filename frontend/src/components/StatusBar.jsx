import { useState } from "react";

const SERVER_HOST = import.meta.env.VITE_MODBUS_HOST || window.location.hostname;
const MODBUS_PORT = import.meta.env.VITE_MODBUS_PORT || "502";

export function StatusBar({ wsStatus, registerCount, onReload, onUpload }) {
  const [copied, setCopied] = useState(false);
  const [reloading, setReloading] = useState(false);
  const address = `${SERVER_HOST}:${MODBUS_PORT}`;

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

  const dot = wsStatus === "open" ? "#22c55e" : wsStatus === "connecting" ? "#f59e0b" : "#ef4444";
  const label = wsStatus === "open" ? "Live" : wsStatus === "connecting" ? "Connecting…" : "Disconnected";

  return (
    <div style={{
      display: "flex", alignItems: "center", gap: "1.5rem",
      padding: "0.6rem 1.25rem",
      background: "#13151C",
      borderBottom: "1px solid #1E2028",
      fontSize: "0.75rem",
      flexWrap: "wrap",
    }}>
      {/* Status dot */}
      <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
        <span style={{
          width: 8, height: 8, borderRadius: "50%",
          background: dot,
          boxShadow: `0 0 6px ${dot}`,
          display: "inline-block",
          animation: wsStatus === "open" ? "pulse 2s infinite" : "none"
        }} />
        <span style={{ color: "#aaa" }}>{label}</span>
      </div>

      {/* Modbus address */}
      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
        <span style={{ color: "#555" }}>Modbus TCP</span>
        <code style={{
          background: "#0D0F14", border: "1px solid #1E2028",
          padding: "0.15rem 0.5rem", borderRadius: "3px", color: "#00D4AA",
          fontSize: "0.72rem",
        }}>{address}</code>
        <button onClick={copy} style={{
          background: "none", border: "1px solid #1E2028",
          borderRadius: "3px", color: copied ? "#22c55e" : "#666",
          padding: "0.15rem 0.5rem", cursor: "pointer", fontSize: "0.68rem"
        }}>
          {copied ? "✓ Copied" : "Copy"}
        </button>
      </div>

      {/* Register count */}
      <span style={{ color: "#555" }}>
        <span style={{ color: "#aaa" }}>{registerCount}</span> registers
      </span>

      <div style={{ marginLeft: "auto", display: "flex", gap: "0.5rem" }}>
        {/* Upload CSV */}
        <label style={{
          background: "#1E2028", border: "1px solid #2a2d38",
          borderRadius: "4px", color: "#aaa", padding: "0.3rem 0.75rem",
          cursor: "pointer", fontSize: "0.72rem"
        }}>
          ⬆ Upload CSV
          <input type="file" accept=".csv" onChange={handleFile} style={{ display: "none" }} />
        </label>

        {/* Reload */}
        <button onClick={handleReload} disabled={reloading} style={{
          background: "#1E2028", border: "1px solid #2a2d38",
          borderRadius: "4px", color: reloading ? "#555" : "#aaa",
          padding: "0.3rem 0.75rem", cursor: "pointer", fontSize: "0.72rem"
        }}>
          {reloading ? "Reloading…" : "↺ Reload CSV"}
        </button>
      </div>

      <style>{`@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }`}</style>
    </div>
  );
}
