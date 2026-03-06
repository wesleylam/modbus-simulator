import { useState, useRef, useEffect } from "react";

const TYPE_COLORS = {
  holding: "#6C63FF",
  input:   "#00D4AA",
  coil:    "#FF6B35",
  discrete:"#F7C59F",
};
const TYPES = ["holding", "input", "coil", "discrete"];

const td = { padding: "0.5rem 1rem", verticalAlign: "middle" };

function Btn({ color, onClick, disabled, children }) {
  return (
    <button onClick={onClick} disabled={disabled} style={{
      background: `${color}22`, border: `1px solid ${color}55`,
      borderRadius: 3, color: disabled ? "#555" : color,
      padding: "0.15rem 0.5rem", cursor: disabled ? "default" : "pointer",
      fontSize: "0.68rem", fontFamily: "inherit"
    }}>{children}</button>
  );
}

const inputStyle = {
  background: "#0D0F14", border: "1px solid #2a2d38", borderRadius: 3,
  color: "#fff", padding: "0.2rem 0.5rem", fontSize: "0.75rem", fontFamily: "inherit"
};

// ── Inline value edit cell ────────────────────────────────────────────────────
function ValueCell({ value, writable, onSave }) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(String(value));
  const [error, setError] = useState(null);
  const ref = useRef(null);

  useEffect(() => { if (editing) ref.current?.select(); }, [editing]);
  useEffect(() => { if (!editing) setDraft(String(value)); }, [value, editing]);

  const commit = async () => {
    const parsed = Number(draft);
    if (isNaN(parsed)) { setError("Must be a number"); return; }
    try { await onSave(parsed); setEditing(false); setError(null); }
    catch (e) { setError(e.message); }
  };

  if (!writable) return <span style={{ color: "#555", fontStyle: "italic" }}>{String(value)}</span>;

  if (editing) return (
    <div style={{ display: "flex", gap: "0.3rem", alignItems: "center" }}>
      <input ref={ref} value={draft} onChange={e => setDraft(e.target.value)}
        onKeyDown={e => { if (e.key === "Enter") commit(); if (e.key === "Escape") setEditing(false); }}
        style={{ ...inputStyle, width: 70 }} />
      <Btn color="#6C63FF" onClick={commit}>✓</Btn>
      <Btn color="#444" onClick={() => { setEditing(false); setError(null); }}>✕</Btn>
      {error && <span style={{ color: "#ef4444", fontSize: "0.62rem" }}>{error}</span>}
    </div>
  );

  return (
    <span onClick={() => setEditing(true)} title="Click to edit"
      style={{ color: "#fff", cursor: "pointer", borderBottom: "1px dashed #333", paddingBottom: 1 }}>
      {String(value)}
    </span>
  );
}

// ── Edit metadata row (inline) ────────────────────────────────────────────────
function EditRow({ reg, onSave, onCancel }) {
  const [name, setName] = useState(reg.name);
  const [type, setType] = useState(reg.type);
  const [writable, setWritable] = useState(reg.writable);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  const commit = async () => {
    if (!name.trim()) { setError("Name required"); return; }
    setSaving(true);
    try { await onSave({ name: name.trim(), type, writable }); }
    catch (e) { setError(e.message); setSaving(false); }
  };

  return (
    <tr style={{ background: "#1a1d25" }}>
      <td style={td}><span style={{ color: "#888", fontFamily: "monospace" }}>{reg.address}</span></td>
      <td style={td}>
        <select value={type} onChange={e => setType(e.target.value)} style={{ ...inputStyle, width: 90 }}>
          {TYPES.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
      </td>
      <td style={td}>
        <input value={name} onChange={e => setName(e.target.value)}
          onKeyDown={e => { if (e.key === "Enter") commit(); if (e.key === "Escape") onCancel(); }}
          style={{ ...inputStyle, width: 150 }} />
        {error && <span style={{ color: "#ef4444", fontSize: "0.62rem", marginLeft: 6 }}>{error}</span>}
      </td>
      <td style={td}><span style={{ color: "#555" }}>—</span></td>
      <td style={td}>
        <select value={writable ? "RW" : "R"} onChange={e => setWritable(e.target.value === "RW")}
          style={{ ...inputStyle, width: 65 }}>
          <option value="RW">R/W</option>
          <option value="R">R</option>
        </select>
      </td>
      <td style={td}>
        <div style={{ display: "flex", gap: "0.3rem" }}>
          <Btn color="#00D4AA" onClick={commit} disabled={saving}>{saving ? "…" : "Save"}</Btn>
          <Btn color="#555" onClick={onCancel}>Cancel</Btn>
        </div>
      </td>
    </tr>
  );
}

// ── Add new register row ──────────────────────────────────────────────────────
function AddRow({ onAdd, onCancel }) {
  const [address, setAddress] = useState("");
  const [name, setName] = useState("");
  const [type, setType] = useState("holding");
  const [value, setValue] = useState("0");
  const [writable, setWritable] = useState(true);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  const commit = async () => {
    const addr = parseInt(address);
    if (isNaN(addr) || addr < 0) { setError("Valid address required"); return; }
    if (!name.trim()) { setError("Name required"); return; }
    const val = parseInt(value);
    if (isNaN(val)) { setError("Value must be a number"); return; }
    setSaving(true);
    try { await onAdd({ address: addr, name: name.trim(), type, value: val, writable }); }
    catch (e) { setError(e.message); setSaving(false); }
  };

  return (
    <tr style={{ background: "#0f1118", borderTop: "1px solid #6C63FF33" }}>
      <td style={td}>
        <input value={address} onChange={e => setAddress(e.target.value)} placeholder="addr"
          style={{ ...inputStyle, width: 55 }} />
      </td>
      <td style={td}>
        <select value={type} onChange={e => setType(e.target.value)} style={{ ...inputStyle, width: 90 }}>
          {TYPES.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
      </td>
      <td style={td}>
        <input value={name} onChange={e => setName(e.target.value)} placeholder="name"
          onKeyDown={e => { if (e.key === "Enter") commit(); if (e.key === "Escape") onCancel(); }}
          style={{ ...inputStyle, width: 150 }} />
        {error && <span style={{ color: "#ef4444", fontSize: "0.62rem", marginLeft: 6 }}>{error}</span>}
      </td>
      <td style={td}>
        <input value={value} onChange={e => setValue(e.target.value)} placeholder="0"
          style={{ ...inputStyle, width: 60 }} />
      </td>
      <td style={td}>
        <select value={writable ? "RW" : "R"} onChange={e => setWritable(e.target.value === "RW")}
          style={{ ...inputStyle, width: 65 }}>
          <option value="RW">R/W</option>
          <option value="R">R</option>
        </select>
      </td>
      <td style={td}>
        <div style={{ display: "flex", gap: "0.3rem" }}>
          <Btn color="#6C63FF" onClick={commit} disabled={saving}>{saving ? "…" : "Add"}</Btn>
          <Btn color="#555" onClick={onCancel}>Cancel</Btn>
        </div>
      </td>
    </tr>
  );
}

// ── Main table ────────────────────────────────────────────────────────────────
export function RegisterTable({ registers, onUpdate, onUpdateMeta, onCreate, onDelete }) {
  const [flash, setFlash] = useState({});
  const [editingAddr, setEditingAddr] = useState(null);
  const [adding, setAdding] = useState(false);
  const prevValues = useRef({});

  useEffect(() => {
    const newFlash = {};
    for (const [addr, reg] of Object.entries(registers)) {
      if (prevValues.current[addr] !== undefined && prevValues.current[addr] !== reg.value)
        newFlash[addr] = true;
      prevValues.current[addr] = reg.value;
    }
    if (Object.keys(newFlash).length) {
      setFlash(newFlash);
      setTimeout(() => setFlash({}), 800);
    }
  }, [registers]);

  const sorted = Object.values(registers).sort((a, b) => a.address - b.address);

  return (
    <div style={{ overflowX: "auto" }}>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.78rem" }}>
        <thead>
          <tr style={{ borderBottom: "1px solid #1E2028" }}>
            {["Addr", "Type", "Name", "Value", "Access", "Actions"].map(h => (
              <th key={h} style={{ padding: "0.6rem 1rem", textAlign: "left",
                color: "#555", fontWeight: 600, fontSize: "0.68rem", letterSpacing: "0.08em" }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map(reg => {
            const typeColor = TYPE_COLORS[reg.type] || "#888";
            if (editingAddr === reg.address) {
              return (
                <EditRow key={reg.address} reg={reg}
                  onSave={async (meta) => { await onUpdateMeta(reg.address, meta); setEditingAddr(null); }}
                  onCancel={() => setEditingAddr(null)} />
              );
            }
            return (
              <tr key={reg.address} style={{
                borderBottom: "1px solid #13151C",
                background: flash[reg.address] ? "#6C63FF10" : "transparent",
                transition: "background 0.3s",
              }}>
                <td style={td}><span style={{ color: "#888", fontFamily: "monospace" }}>{reg.address}</span></td>
                <td style={td}>
                  <span style={{ background: `${typeColor}18`, border: `1px solid ${typeColor}40`,
                    color: typeColor, borderRadius: 3, padding: "0.1rem 0.45rem",
                    fontSize: "0.65rem", fontWeight: 700 }}>{reg.type}</span>
                </td>
                <td style={td}><span style={{ color: "#ccc" }}>{reg.name}</span></td>
                <td style={td}>
                  <ValueCell value={reg.value} writable={reg.writable}
                    onSave={(v) => onUpdate(reg.address, v)} />
                </td>
                <td style={td}>
                  <span style={{ color: reg.writable ? "#22c55e" : "#555", fontSize: "0.7rem" }}>
                    {reg.writable ? "R/W" : "R"}
                  </span>
                </td>
                <td style={td}>
                  <div style={{ display: "flex", gap: "0.3rem" }}>
                    <Btn color="#6C63FF" onClick={() => { setAdding(false); setEditingAddr(reg.address); }}>Edit</Btn>
                    <Btn color="#ef4444" onClick={() => {
                      if (window.confirm(`Delete register ${reg.address} (${reg.name})?`)) onDelete(reg.address);
                    }}>Delete</Btn>
                  </div>
                </td>
              </tr>
            );
          })}

          {adding
            ? <AddRow
                onAdd={async (data) => { await onCreate(data); setAdding(false); }}
                onCancel={() => setAdding(false)} />
            : (
              <tr>
                <td colSpan={6} style={{ padding: "0.5rem 1rem" }}>
                  <button
                    onClick={() => { setEditingAddr(null); setAdding(true); }}
                    style={{
                      background: "none", border: "1px dashed #2a2d38",
                      borderRadius: 4, color: "#555", padding: "0.35rem 1rem",
                      cursor: "pointer", fontSize: "0.72rem", width: "100%",
                      transition: "color 0.15s, border-color 0.15s",
                    }}
                    onMouseEnter={e => { e.currentTarget.style.color="#6C63FF"; e.currentTarget.style.borderColor="#6C63FF55"; }}
                    onMouseLeave={e => { e.currentTarget.style.color="#555"; e.currentTarget.style.borderColor="#2a2d38"; }}
                  >+ Add register</button>
                </td>
              </tr>
            )
          }
        </tbody>
      </table>
    </div>
  );
}
