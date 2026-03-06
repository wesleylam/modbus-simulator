import { useRegisters } from "./hooks/useRegisters";
import { StatusBar } from "./components/StatusBar";
import { RegisterTable } from "./components/RegisterTable";
import { ChangeLog } from "./components/ChangeLog";

export default function App() {
  const {
    registers, changeLog, loading, wsStatus,
    updateRegister, reloadConfig, uploadCsv,
  } = useRegisters();

  const registerCount = Object.keys(registers).length;

  return (
    <div style={{
      fontFamily: "'DM Mono', 'Courier New', monospace",
      background: "#0D0F14",
      minHeight: "100vh",
      color: "#E8E8E8",
    }}>
      {/* Top bar */}
      <StatusBar
        wsStatus={wsStatus}
        registerCount={registerCount}
        onReload={reloadConfig}
        onUpload={uploadCsv}
      />

      {/* Page header */}
      <div style={{ padding: "1.5rem 1.5rem 0" }}>
        <div style={{ fontSize: "0.6rem", color: "#444", letterSpacing: "0.2em", marginBottom: "0.3rem" }}>
          MODBUS TCP SIMULATOR
        </div>
        <h1 style={{ margin: 0, fontSize: "1.3rem", fontWeight: 700, color: "#fff", letterSpacing: "-0.02em" }}>
          Register Dashboard
        </h1>
      </div>

      <div style={{ padding: "1.25rem 1.5rem", display: "flex", flexDirection: "column", gap: "1.25rem" }}>

        {/* Register table */}
        <section style={{
          background: "#13151C",
          border: "1px solid #1E2028",
          borderRadius: "8px",
          overflow: "hidden",
        }}>
          <div style={{
            padding: "0.75rem 1rem",
            borderBottom: "1px solid #1E2028",
            display: "flex", alignItems: "center", justifyContent: "space-between"
          }}>
            <span style={{ fontSize: "0.72rem", fontWeight: 600, color: "#888", letterSpacing: "0.1em" }}>
              REGISTERS
            </span>
            <span style={{ fontSize: "0.68rem", color: "#444" }}>
              Click a value to edit (R/W only)
            </span>
          </div>

          {loading ? (
            <div style={{ padding: "2rem", textAlign: "center", color: "#555", fontSize: "0.8rem" }}>
              Connecting to server…
            </div>
          ) : (
            <RegisterTable registers={registers} onUpdate={updateRegister} />
          )}
        </section>

        {/* Change log */}
        <section style={{
          background: "#13151C",
          border: "1px solid #1E2028",
          borderRadius: "8px",
          overflow: "hidden",
        }}>
          <div style={{
            padding: "0.75rem 1rem",
            borderBottom: "1px solid #1E2028",
            display: "flex", alignItems: "center", justifyContent: "space-between"
          }}>
            <span style={{ fontSize: "0.72rem", fontWeight: 600, color: "#888", letterSpacing: "0.1em" }}>
              CHANGE LOG
            </span>
            <span style={{ fontSize: "0.68rem", color: "#444" }}>
              {changeLog.length} events
            </span>
          </div>
          <ChangeLog log={changeLog} registers={registers} />
        </section>
      </div>
    </div>
  );
}
