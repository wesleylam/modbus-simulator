import { useState, useEffect, useRef, useCallback } from "react";

const WS_URL = import.meta.env.VITE_WS_URL || `ws://${window.location.hostname}:8000/ws`;

export function useWebSocket(onMessage) {
  const [status, setStatus] = useState("connecting"); // connecting | open | closed
  const wsRef = useRef(null);
  const retryRef = useRef(null);
  const retryCount = useRef(0);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;
    setStatus("connecting");

    ws.onopen = () => {
      setStatus("open");
      retryCount.current = 0;
    };

    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        onMessage(data);
      } catch (err) {
        console.warn("Failed to parse WS message", err);
      }
    };

    ws.onclose = () => {
      setStatus("closed");
      // Exponential backoff: 1s, 2s, 4s, max 10s
      const delay = Math.min(1000 * 2 ** retryCount.current, 10000);
      retryCount.current++;
      retryRef.current = setTimeout(connect, delay);
    };

    ws.onerror = () => {
      ws.close();
    };
  }, [onMessage]);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(retryRef.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return status;
}
