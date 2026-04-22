import React from "react";

export default function ModeSelector({ mode, setMode }) {
  return (
    <div style={{ display: "flex", gap: 10 }}>
      <button
        onClick={() => setMode("file")}
        style={{ background: mode === "file" ? "#000" : "#ccc", color: "#fff" }}
      >
        File Mode
      </button>

      <button
        onClick={() => setMode("realtime")}
        style={{ background: mode === "realtime" ? "#000" : "#ccc", color: "#fff" }}
      >
        Real-Time Mode
      </button>
    </div>
  );
}