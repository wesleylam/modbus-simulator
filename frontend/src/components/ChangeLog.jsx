const SOURCE_COLORS = { modbus: "#FF6B35", api: "#6C63FF" };

export function ChangeLog({ log, registers }) {
  if (!log.length) {
    return (
      <div style={{ color: "#555", padding: "2rem", textAlign: "center", fontSize: "0.8rem" }}>
        No changes yet — write to a register via Modbus or the table above
      </div>
    );
  }

  return (
    <div style={{ overflowY: "auto", maxHeight: "340px" }}>
      {log.map((evt) => {
        const reg = registers[evt.address];
        const srcColor = SOURCE_COLORS[evt.source] || "#888";
        return (
          <div key={evt._id} style={{
            display: "flex", alignItems: "center", gap: "0.75rem",
            padding: "0.5rem 1rem",
            borderBottom: "1px solid #0D0F14",
            fontSize: "0.73rem",
            animation: "slideIn 0.15s ease",
          }}>
            {/* Timestamp */}
            <span style={{ color: "#444", fontFamily: "monospace", fontSize: "0.68rem", whiteSpace: "nowrap" }}>
              {new Date(evt.timestamp * 1000).toLocaleTimeString()}
            </span>

            {/* Source badge */}
            <span style={{
              background: `${srcColor}18`, border: `1px solid ${srcColor}40`,
              color: srcColor, borderRadius: "3px", padding: "0.1rem 0.45rem",
              fontSize: "0.64rem", fontWeight: 700, whiteSpace: "nowrap"
            }}>
              {evt.source === "modbus" ? "MODBUS" : "DASHBOARD"}
              {evt.client_ip ? ` · ${evt.client_ip}` : ""}
            </span>

            {/* Register name + address */}
            <span style={{ color: "#aaa", flex: 1 }}>
              {reg?.name || `Register ${evt.address}`}
              <span style={{ color: "#444", marginLeft: "0.3rem" }}>#{evt.address}</span>
            </span>

            {/* Delta */}
            <span style={{ fontFamily: "monospace", whiteSpace: "nowrap" }}>
              <span style={{ color: "#ef4444" }}>{String(evt.old_value)}</span>
              <span style={{ color: "#444", margin: "0 0.3rem" }}>→</span>
              <span style={{ color: "#22c55e" }}>{String(evt.new_value)}</span>
            </span>
          </div>
        );
      })}
      <style>{`@keyframes slideIn { from{opacity:0;transform:translateY(-4px)} to{opacity:1;transform:none} }`}</style>
    </div>
  );
}
