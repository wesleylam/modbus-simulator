import { useState, useCallback, useRef } from "react";
import { useWebSocket } from "./useWebSocket";

const API_BASE = import.meta.env.VITE_API_URL || `http://${window.location.hostname}:8000`;

export function useRegisters() {
  const [registers, setRegisters] = useState({});
  const [changeLog, setChangeLog] = useState([]);
  const [loading, setLoading] = useState(true);
  const logIdRef = useRef(0);

  const addToLog = useCallback((evt) => {
    setChangeLog((prev) => [
      { ...evt, _id: logIdRef.current++ },
      ...prev.slice(0, 199),
    ]);
  }, []);

  const handleMessage = useCallback((msg) => {
    if (msg.type === "snapshot") {
      const map = {};
      for (const r of msg.registers) map[r.address] = r;
      setRegisters(map);
      setLoading(false);
    } else if (msg.type === "update") {
      setRegisters((prev) => ({
        ...prev,
        [msg.address]: { ...prev[msg.address], value: msg.new_value, last_changed: msg.timestamp },
      }));
      addToLog(msg);
    } else if (msg.type === "add") {
      // Re-fetch the new register from the API
      fetch(`${API_BASE}/registers/${msg.address}`)
        .then(r => r.json())
        .then(reg => setRegisters(prev => ({ ...prev, [reg.address]: reg })));
      addToLog(msg);
    } else if (msg.type === "remove") {
      setRegisters((prev) => {
        const next = { ...prev };
        delete next[msg.address];
        return next;
      });
      addToLog(msg);
    } else if (msg.type === "meta") {
      fetch(`${API_BASE}/registers/${msg.address}`)
        .then(r => r.json())
        .then(reg => setRegisters(prev => ({ ...prev, [reg.address]: reg })));
    } else if (msg.type === "unit_id_changed") {
      addToLog({ ...msg, _label: `Unit ID: ${msg.old_value} → ${msg.new_value}` });
    }
  }, [addToLog]);

  const wsStatus = useWebSocket(handleMessage);

  const updateValue = useCallback(async (address, value) => {
    const res = await fetch(`${API_BASE}/registers/${address}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ value }),
    });
    if (!res.ok) { const e = await res.json(); throw new Error(e.detail || "Update failed"); }
    return res.json();
  }, []);

  const createRegister = useCallback(async ({ address, name, type, value, writable }) => {
    const res = await fetch(`${API_BASE}/registers/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ address, name, type, value, writable }),
    });
    if (!res.ok) { const e = await res.json(); throw new Error(e.detail || "Create failed"); }
    return res.json();
  }, []);

  const updateMeta = useCallback(async (address, { name, type, writable }) => {
    const res = await fetch(`${API_BASE}/registers/${address}/meta`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, type, writable }),
    });
    if (!res.ok) { const e = await res.json(); throw new Error(e.detail || "Edit failed"); }
    return res.json();
  }, []);

  const deleteRegister = useCallback(async (address) => {
    const res = await fetch(`${API_BASE}/registers/${address}`, { method: "DELETE" });
    if (!res.ok) { const e = await res.json(); throw new Error(e.detail || "Delete failed"); }
    return res.json();
  }, []);

  const reloadConfig = useCallback(async () => {
    const res = await fetch(`${API_BASE}/config/reload`, { method: "POST" });
    if (!res.ok) throw new Error("Reload failed");
    return res.json();
  }, []);

  const uploadCsv = useCallback(async (file) => {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${API_BASE}/config/upload`, { method: "POST", body: form });
    if (!res.ok) { const e = await res.json(); throw new Error(e.detail || "Upload failed"); }
    return res.json();
  }, []);

  return {
    registers, changeLog, loading, wsStatus,
    updateValue, createRegister, updateMeta, deleteRegister,
    reloadConfig, uploadCsv,
  };
}
