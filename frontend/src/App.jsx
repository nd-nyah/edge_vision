import React, { useState, useRef } from "react";

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

  // ✅ ADDED: progress state
  const [progress, setProgress] = useState(0);

  const readerRef = useRef(null);

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

  const startStream = async () => {
    setStatus("running");
    setProgress(0);

    const res = await fetch(`${API}/api/video`);
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

        const data = JSON.parse(part);

        // =========================
        // FRAME UPDATE
        // =========================
        if (data.image) setFrame(data.image);

        if (data.detections) setDetections(data.detections);

        // =========================
        // PROGRESS UPDATE
        // =========================
        if (data.progress !== undefined) {
          setProgress(data.progress);
        }

        // =========================
        // END SIGNAL
        // =========================
        if (data.status === "detection_completed") {
          setStatus("done");
          setProgress(100);
          setFrame(null);
          setDetections([]);
          return;
        }
      }
    }
  };

  const stopStream = async () => {
    setStatus("stopped");
    if (readerRef.current) {
      await readerRef.current.cancel();
    }
  };

  return (
    <div style={{ maxWidth: 800, margin: "auto", padding: 20 }}>

      <h2>🎥 Upload</h2>

      <input type="file" accept="video/*" onChange={handleFileChange} />

      {preview && (
        <video width="100%" controls src={preview} />
      )}

      <button onClick={handleUpload} disabled={uploading}>
        {uploading ? "Uploading..." : "Upload"}
      </button>

      {success && <p>✅ Uploaded</p>}
      {error && <p style={{ color: "red" }}>{error}</p>}

      <hr />

      <h2>🧠 Detection</h2>

      <button onClick={startStream}>▶ Start Stream</button>
      <button onClick={stopStream}>⏹ Stop</button>

      <p>Status: {status}</p>

      {/* ✅ PROGRESS UI */}
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
            transition: "width 0.2s"
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

      {detections.length > 0 && (
        <ul>
          {detections.map((d, i) => (
            <li key={i}>
              {d.label} ({Math.round(d.confidence * 100)}%)
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}