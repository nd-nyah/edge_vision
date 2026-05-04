import "./styles/banner.css";
import React, { useState, useRef, useEffect } from "react";

const API = import.meta.env.VITE_API_URL;

export default function App() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);

  const [uploading, setUploading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState(null);

  const [frame, setFrame] = useState(null);
  const [detections, setDetections] = useState([]);
  const [status, setStatus] = useState("idle");

  const [progress, setProgress] = useState(0);

  const [prompt, setPrompt] = useState("person, car");

  const readerRef = useRef(null);

  // =========================
  // FILE HANDLING
  // =========================
  const handleFileChange = (e) => {
    const f = e.target.files[0];
    if (!f) return;

    setFile(f);
    setPreview(URL.createObjectURL(f));

    setFrame(null);
    setDetections([]);
    setProgress(0);
    setStatus("idle");
  };

  // =========================
  // UPLOAD VIDEO
  // =========================
  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch(`${API}/api/upload-video`, {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Upload failed");

      setSuccess(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  // =========================
  // START STREAM
  // =========================
  const startStream = async () => {
    setStatus("running");
    setProgress(0);

    const cleanedPrompts = prompt
      .split(",")
      .map(p => p.trim().toLowerCase())
      .filter(Boolean);

    // 🔥 send prompts (this triggers YOLO-World automatically in backend)
    try {
      await fetch(`${API}/api/set-prompts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompts: cleanedPrompts }),
      });
    } catch (err) {
      console.error("Prompt error:", err);
    }

    const res = await fetch(`${API}/api/video`);

    if (!res.ok || !res.body) {
      setStatus("error");
      return;
    }

    const reader = res.body.getReader();
    readerRef.current = reader;

    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      const parts = buffer.split("\n");
      buffer = parts.pop();

      for (const part of parts) {
        if (!part.trim()) continue;

        // 🔥 safe JSON parsing
        let data;
        try {
          data = JSON.parse(part);
        } catch {
          continue;
        }

        if (data.image) setFrame(data.image);
        if (Array.isArray(data.detections)) setDetections(data.detections);
        if (data.progress !== undefined) setProgress(data.progress);

        if (data.status === "done") {
          setStatus("done");
          setProgress(100);
          return;
        }
      }
    }
  };

  // =========================
  // STOP STREAM
  // =========================
  const stopStream = async () => {
    setStatus("stopped");
    if (readerRef.current) {
      await readerRef.current.cancel();
    }
  };

  // =========================
  // CLEANUP
  // =========================
  useEffect(() => {
    return () => {
      if (preview) URL.revokeObjectURL(preview);
    };
  }, [preview]);

  // =========================
  // UI
  // =========================
  return (
    <div style={{ maxWidth: 800, margin: "auto", padding: 20 }}>

      <div className="banner">
        <div className="banner-text">
          Altitude - Drone Vision 🚁 • Altitude - Drone Vision 🚁
        </div>
      </div>

      <h2>🎥 Upload</h2>

      <input type="file" accept="video/*" onChange={handleFileChange} />

      {preview && <video width="100%" controls src={preview} />}

      <button onClick={handleUpload} disabled={uploading}>
        {uploading ? "Uploading..." : "Upload"}
      </button>

      {success && <p>✅ Uploaded</p>}
      {error && <p style={{ color: "red" }}>{error}</p>}

      <hr />

      <h2>🔎 Prompt (auto switches YOLO → YOLO-World)</h2>

      <input
        type="text"
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="e.g. person, car"
        style={{
          width: "100%",
          padding: 10,
          borderRadius: 6,
          border: "1px solid #ccc",
          marginBottom: 10,
        }}
      />

      <hr />

      <h2>🧠 Detection</h2>

      <button onClick={startStream}>▶ Start Stream</button>
      <button onClick={stopStream}>⏹ Stop</button>

      <p>Status: {status}</p>

      <p>
        Progress: [
        <span style={{ color: "green" }}>
          {"█".repeat(Math.round(progress / 5))}
        </span>
        <span style={{ color: "#ddd" }}>
          {"░".repeat(20 - Math.round(progress / 5))}
        </span>
        ] {progress.toFixed(1)}%
      </p>

      <div style={{ width: "100%", background: "#eee", borderRadius: 5 }}>
        <div
          style={{
            width: `${progress}%`,
            height: 8,
            background: "green",
            borderRadius: 5,
            transition: "width 0.2s",
          }}
        />
      </div>

      {frame ? (
        <img
          src={`data:image/jpeg;base64,${frame}`}
          style={{ width: "100%", marginTop: 20 }}
        />
      ) : (
        <p>No stream yet</p>
      )}

      {detections.length > 0 ? (
        <ul>
          {detections.map((d, i) => (
            <li key={i}>
              {d.label} ({Math.round(d.confidence * 100)}%)
            </li>
          ))}
        </ul>
      ) : (
        <p style={{ opacity: 0.6 }}>No matching objects detected</p>
      )}
    </div>
  );
}
