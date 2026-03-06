import { useState, useCallback, useRef } from "react";
import { useWebSocket } from "./useWebSocket";

const API_BASE = import.meta.env.VITE_API_URL || `http://${window.location.hostname}:8000`;

export function useRegisters() {
  const [registers, setRegisters] = useState({}); // keyed by address
  const [changeLog, setChangeLog] = useState([]);  // latest first
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const logIdRef = useRef(0);

  const addToLog = useCallback((evt) => {
    setChangeLog((prev) => [
      { ...evt, _id: logIdRef.current++ },
      ...prev.slice(0, 199), // keep last 200 entries
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
        [msg.address]: {
          ...prev[msg.address],
          value: msg.new_value,
          last_changed: msg.timestamp,
        },
      }));
      addToLog(msg);
    }
  }, [addToLog]);

  const wsStatus = useWebSocket(handleMessage);

  const updateRegister = useCallback(async (address, value) => {
    const res = await fetch(`${API_BASE}/registers/${address}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ value }),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Update failed");
    }
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
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Upload failed");
    }
    return res.json();
  }, []);

  return {
    registers,
    changeLog,
    loading,
    error,
    wsStatus,
    updateRegister,
    reloadConfig,
    uploadCsv,
  };
}
