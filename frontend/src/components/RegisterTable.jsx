import { useState, useRef, useEffect } from "react";

const TYPE_COLORS = {
  holding: "#6C63FF",
  input:   "#00D4AA",
  coil:    "#FF6B35",
  discrete:"#F7C59F",
};

function EditableCell({ value, writable, onSave }) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(String(value));
  const [error, setError] = useState(null);
  const inputRef = useRef(null);

  useEffect(() => {
    if (editing) inputRef.current?.select();
  }, [editing]);

  const commit = async () => {
    const parsed = Number(draft);
    if (isNaN(parsed)) { setError("Must be a number"); return; }
    try {
      await onSave(parsed);
      setEditing(false);
      setError(null);
    } catch (e) {
      setError(e.message);
    }
  };

  if (!writable) {
    return <span style={{ color: "#666", fontStyle: "italic" }}>{String(value)}</span>;
  }

  if (editing) {
    return (
      <div style={{ display: "flex", gap: "0.3rem", alignItems: "center" }}>
        <input
          ref={inputRef}
          value={draft}
          onChange={e => setDraft(e.target.value)}
          onKeyDown={e => { if (e.key === "Enter") commit(); if (e.key === "Escape") setEditing(false); }}
          style={{
            width: "80px", background: "#0D0F14", border: `1px solid ${error ? "#ef4444" : "#6C63FF"}`,
            borderRadius: "3px", color: "#fff", padding: "0.2rem 0.4rem",
            fontSize: "0.75rem", fontFamily: "inherit"
          }}
        />
        <button onClick={commit} style={{
          background: "#6C63FF22", border: "1px solid #6C63FF55",
          borderRadius: "3px", color: "#6C63FF", padding: "0.15rem 0.4rem",
          cursor: "pointer", fontSize: "0.68rem"
        }}>✓</button>
        <button onClick={() => { setEditing(false); setError(null); }} style={{
          background: "none", border: "1px solid #333",
          borderRadius: "3px", color: "#666", padding: "0.15rem 0.4rem",
          cursor: "pointer", fontSize: "0.68rem"
        }}>✕</button>
        {error && <span style={{ color: "#ef4444", fontSize: "0.65rem" }}>{error}</span>}
      </div>
    );
  }

  return (
    <span
      onClick={() => { setDraft(String(value)); setEditing(true); }}
      style={{
        color: "#fff", cursor: "pointer", borderBottom: "1px dashed #333",
        paddingBottom: "1px"
      }}
      title="Click to edit"
    >
      {String(value)}
    </span>
  );
}

export function RegisterTable({ registers, onUpdate }) {
  const [flash, setFlash] = useState({});
  const prevValues = useRef({});

  // Flash rows that just changed
  useEffect(() => {
    const newFlash = {};
    for (const [addr, reg] of Object.entries(registers)) {
      if (prevValues.current[addr] !== undefined && prevValues.current[addr] !== reg.value) {
        newFlash[addr] = true;
      }
      prevValues.current[addr] = reg.value;
    }
    if (Object.keys(newFlash).length) {
      setFlash(newFlash);
      setTimeout(() => setFlash({}), 800);
    }
  }, [registers]);

  const sorted = Object.values(registers).sort((a, b) => a.address - b.address);

  if (!sorted.length) {
    return <div style={{ color: "#555", padding: "2rem", textAlign: "center", fontSize: "0.8rem" }}>
      No registers loaded
    </div>;
  }

  return (
    <div style={{ overflowX: "auto" }}>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.78rem" }}>
        <thead>
          <tr style={{ borderBottom: "1px solid #1E2028" }}>
            {["Addr", "Type", "Name", "Value", "Access", "Last Changed"].map(h => (
              <th key={h} style={{
                padding: "0.6rem 1rem", textAlign: "left",
                color: "#555", fontWeight: 600, fontSize: "0.68rem",
                letterSpacing: "0.08em", whiteSpace: "nowrap"
              }}>{h.toUpperCase()}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map(reg => {
            const typeColor = TYPE_COLORS[reg.type] || "#888";
            const isFlashing = flash[reg.address];
            return (
              <tr key={reg.address} style={{
                borderBottom: "1px solid #13151C",
                background: isFlashing ? "#6C63FF10" : "transparent",
                transition: "background 0.3s",
              }}>
                <td style={{ padding: "0.55rem 1rem", color: "#888", fontFamily: "monospace" }}>
                  {reg.address}
                </td>
                <td style={{ padding: "0.55rem 1rem" }}>
                  <span style={{
                    background: `${typeColor}18`, border: `1px solid ${typeColor}40`,
                    color: typeColor, borderRadius: "3px", padding: "0.1rem 0.45rem",
                    fontSize: "0.65rem", fontWeight: 700
                  }}>{reg.type}</span>
                </td>
                <td style={{ padding: "0.55rem 1rem", color: "#ccc" }}>{reg.name}</td>
                <td style={{ padding: "0.55rem 1rem" }}>
                  <EditableCell
                    value={reg.value}
                    writable={reg.writable}
                    onSave={(v) => onUpdate(reg.address, v)}
                  />
                </td>
                <td style={{ padding: "0.55rem 1rem" }}>
                  <span style={{ color: reg.writable ? "#22c55e" : "#555", fontSize: "0.7rem" }}>
                    {reg.writable ? "R/W" : "R"}
                  </span>
                </td>
                <td style={{ padding: "0.55rem 1rem", color: "#444", fontFamily: "monospace", fontSize: "0.7rem" }}>
                  {reg.last_changed
                    ? new Date(reg.last_changed * 1000).toLocaleTimeString()
                    : "—"}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
