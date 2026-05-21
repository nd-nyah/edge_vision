import "./styles/banner.css";
import React, { useState, useRef, useEffect } from "react";

const API = import.meta.env.VITE_API_URL;

/**
 * App State Model
 */
const initialUIState = {
  mode: "camera",

  upload: {
    file: null,
    preview: null,
    status: "idle",
    error: null,
  },

  stream: {
    status: "idle",
    frame: null,
    detections: [],
    progress: 0,
  },

  agent: {
    mode: "HIGH",
    objectCount: 0,
    detectInterval: 1,
  },

  metrics: {
    fps: 0,
    baselineLatency: 0,
    agentLatency: 0,
    loadRatio: 0,
  },

  prompt: "person, car",
};

export default function App() {
  const [state, setState] = useState(initialUIState);

  // ==========================
  // TOAST
  // ==========================
  const [toast, setToast] = useState(null);

  const showToast = (message, type = "success") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 2500);
  };

  const readerRef = useRef(null);
  const abortRef = useRef(false);
  const fpsRef = useRef({ last: Date.now(), count: 0 });

  // ==========================
  // RESET MODE SAFE
  // ==========================
  useEffect(() => {
    abortRef.current = true;
    readerRef.current?.cancel();

    setState((s) => ({
      ...initialUIState,
      mode: s.mode,

      upload:
        s.mode === "video"
          ? { ...s.upload, file: null, preview: null, error: null }
          : { file: null, preview: null, status: "idle", error: null },

      stream: {
        status: "idle",
        frame: null,
        detections: [],
        progress: 0,
      },
    }));
  }, [state.mode]);

  // ==========================
  // FILE
  // ==========================
  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setState((s) => ({
      ...s,
      upload: {
        ...s.upload,
        file,
        preview: URL.createObjectURL(file),
      },
    }));
  };

  // ==========================
  // UPLOAD + POPUP
  // ==========================
  const handleUpload = async () => {
    if (!state.upload.file) return;

    setState((s) => ({
      ...s,
      upload: { ...s.upload, status: "uploading", error: null },
    }));

    try {
      const formData = new FormData();
      formData.append("file", state.upload.file);

      const res = await fetch(`${API}/api/upload-video`, {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Upload failed");

      setState((s) => ({
        ...s,
        upload: { ...s.upload, status: "success" },
        stream: { ...s.stream, status: "ready" },
      }));

      showToast("Upload successful", "success");
    } catch (err) {
      setState((s) => ({
        ...s,
        upload: { ...s.upload, status: "error", error: err.message },
      }));

      showToast("Upload failed", "error");
    }
  };

  // ==========================
  // STREAM
  // ==========================
  const startStream = async () => {
    abortRef.current = false;

    setState((s) => ({
      ...s,
      stream: { ...s.stream, status: "running" },
    }));

    const cleanedPrompts = state.prompt
      .split(",")
      .map((p) => p.trim().toLowerCase())
      .filter(Boolean);

    await fetch(`${API}/api/set-prompts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompts: cleanedPrompts }),
    }).catch(() => {});

    const endpoint =
      state.mode === "camera"
        ? `${API}/api/camera-stream`
        : `${API}/api/video`;

    try {
      const res = await fetch(endpoint);
      if (!res.ok || !res.body) throw new Error("Stream failed");

      const reader = res.body.getReader();
      readerRef.current = reader;

      const decoder = new TextDecoder();
      let buffer = "";

      while (!abortRef.current) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split(/\r?\n/);
        buffer = parts.pop();

        for (const part of parts) {
          if (!part.trim()) continue;

          let data;
          try {
            data = JSON.parse(part);
          } catch {
            continue;
          }

          const img =
            data?.frame ||
            data?.image ||
            data?.agent?.frame ||
            data?.baseline?.frame;

          const det = data?.detections || data?.agent?.detections || [];

          // FPS
          const now = Date.now();
          fpsRef.current.count++;

          if (now - fpsRef.current.last >= 1000) {
            setState((s) => ({
              ...s,
              metrics: { ...s.metrics, fps: fpsRef.current.count },
            }));
            fpsRef.current.count = 0;
            fpsRef.current.last = now;
          }

          // STATE UPDATE (AGENT + METRICS RESTORED)
          setState((s) => ({
            ...s,

            stream: {
              ...s.stream,
              frame: img || s.stream.frame,
              detections: det,
              progress: data?.progress ?? s.stream.progress,
            },

            agent: {
              ...s.agent,
              mode: data?.mode ?? s.agent.mode,
              objectCount: Array.isArray(det) ? det.length : s.agent.objectCount,
              detectInterval: data?.detect_interval ?? s.agent.detectInterval,
            },

            metrics: {
              ...s.metrics,
              baselineLatency: data?.baseline?.latency_ms ?? s.metrics.baselineLatency,
              agentLatency: data?.agent?.latency_ms ?? s.metrics.agentLatency,
              loadRatio: data?.metrics?.load_ratio ?? s.metrics.loadRatio,
            },
          }));

          if (data.status === "done") {
            setState((s) => ({
              ...s,
              stream: { ...s.stream, status: "done" },
            }));
          }
        }
      }
    } catch (err) {
      setState((s) => ({
        ...s,
        stream: { ...s.stream, status: "error" },
      }));
    }
  };

  const stopStream = () => {
    abortRef.current = true;
    readerRef.current?.cancel();

    setState((s) => ({
      ...s,
      stream: { ...s.stream, status: "stopped" },
    }));
  };

  // ==========================
  // UI
  // ==========================
  return (
    <div style={{
      height: "100vh",
      display: "flex",
      flexDirection: "column",
      background: "#070A0F",
      color: "#fff",
      fontFamily: "system-ui",
    }}>

      {/* TOAST */}
      {toast && (
        <div style={{
          position: "fixed",
          top: 20,
          right: 20,
          padding: "10px 14px",
          borderRadius: 8,
          background: toast.type === "error" ? "#b00020" : "#1db954",
          zIndex: 9999,
        }}>
          {toast.message}
        </div>
      )}

      <div className="banner">
        <div className="banner-text">
          Computer Vision • Full Agent Dashboard
        </div>
      </div>

      {/* CONTROLS */}
      <div style={{ display: "flex", gap: 10, padding: 10 }}>
        <button onClick={() => setState((s) => ({ ...s, mode: "camera" }))}>
          🎥 Camera
        </button>

        <button onClick={() => setState((s) => ({ ...s, mode: "video" }))}>
          📁 Video
        </button>

        {state.mode === "video" && (
          <>
            <input type="file" accept="video/*" onChange={handleFileChange} />
            <button onClick={handleUpload}>
              {state.upload.status === "uploading" ? "Uploading..." : "Upload"}
            </button>
          </>
        )}

        <input
          value={state.prompt}
          onChange={(e) =>
            setState((s) => ({ ...s, prompt: e.target.value }))
          }
          style={{ flex: 1 }}
        />

        <button onClick={startStream}>▶</button>
        <button onClick={stopStream}>⏹</button>
      </div>

      {/* MAIN VIEW */}
      <div style={{ flex: 1, display: "flex" }}>

        {/* VIDEO */}
        <div style={{ flex: 3, position: "relative" }}>
          {state.stream.frame ? (
            <img
              src={`data:image/jpeg;base64,${state.stream.frame}`}
              style={{ width: "100%", height: "100%", objectFit: "contain" }}
            />
          ) : (
            <p>No stream</p>
          )}

          <div style={{ position: "absolute", top: 10, right: 10 }}>
            👁 {state.agent.objectCount}
          </div>

          <div style={{ position: "absolute", bottom: 10, left: 10 }}>
            ⚙ FPS: {state.metrics.fps}
          </div>

          <div style={{ position: "absolute", bottom: 10, right: 10 }}>
            🔥 Interval: {state.agent.detectInterval}
          </div>
        </div>

        {/* ✅ RIGHT SIDEBAR (FIXED - WAS MISSING) */}
        <div style={{
          flex: 1,
          borderLeft: "1px solid #222",
          padding: 10
        }}>
          <h3>Agent Dashboard</h3>

          <p>Mode: {state.agent.mode}</p>
          <p>Objects: {state.agent.objectCount}</p>
          <p>Status: {state.stream.status}</p>
          <p>Progress: {state.stream.progress.toFixed(1)}%</p>

          <hr />

          <div style={{
            marginTop: 10,
            padding: 10,
            borderRadius: 8,
            background: "#111",
            border: "1px solid #333",
          }}>
            <p>🔴 Base: {state.metrics.baselineLatency.toFixed(1)} ms</p>
            <p>🟢 Agent: {state.metrics.agentLatency.toFixed(1)} ms</p>
            <p>📊 Load: {state.metrics.loadRatio.toFixed(2)}x</p>
          </div>
        </div>

      </div>
    </div>
  );
}


