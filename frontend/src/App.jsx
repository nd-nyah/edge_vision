import React, { useState } from "react";
import "./styles/banner.css";

const API = import.meta.env.VITE_API_URL;

export default function App() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);

  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  const [uploadedFileName, setUploadedFileName] = useState(null);

  // =========================
  // DETECTION STATE
  // =========================
  const [detecting, setDetecting] = useState(false);
  const [frame, setFrame] = useState(null);
  const [detections, setDetections] = useState([]);
  const [status, setStatus] = useState("idle");

  // =========================
  // FILE SELECT
  // =========================
  const handleFileChange = (e) => {
    const f = e.target.files[0];

    if (f) {
      setFile(f);
      setPreview(URL.createObjectURL(f));
      setError(null);
      setSuccess(false);
      setUploadedFileName(null);
    }
  };

  // =========================
  // UPLOAD
  // =========================
  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setError(null);
    setSuccess(false);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${API}/upload-video`, {
        method: "POST",
        body: formData,
      });

      const text = await res.text();
      const data = JSON.parse(text);

      if (!res.ok) throw new Error(data.detail || "Upload failed");

      setUploadedFileName(data.filename);
      setSuccess(true);

    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  // =========================
  // DELETE
  // =========================
  const handleDelete = async () => {
    if (!uploadedFileName) return;

    try {
      const res = await fetch(
        `${API}/delete-video?filename=${uploadedFileName}`,
        { method: "DELETE" }
      );

      if (!res.ok) throw new Error("Delete failed");

      setFile(null);
      setPreview(null);
      setUploadedFileName(null);
      setSuccess(false);
      setError(null);

      document.querySelector("input[type='file']").value = "";

      alert("Video deleted 🗑");

    } catch (err) {
      alert(err.message);
    }
  };

  // =========================
  // DETECTION START
  // =========================
  const startDetect = async () => {
    try {
      setStatus("starting...");

      const res = await fetch(`${API}/start-detect`, {
        method: "POST",
      });

      const text = await res.text();
      const data = JSON.parse(text || "{}");

      if (!res.ok) throw new Error(data.detail || "Start detect failed");

      setDetecting(true);
      setStatus("running");

    } catch (err) {
      setStatus("error");
      console.error(err);
    }
  };

  // =========================
  // DETECTION STOP
  // =========================
  const stopDetect = async () => {
    try {
      await fetch(`${API}/stop-detect`, {
        method: "POST",
      });

      setDetecting(false);
      setStatus("stopped");

    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div style={{ maxWidth: 800, margin: "auto", padding: 20 }}>
       {/* =========================
          🔥 ROLLING BANNER
      ========================= */}
      <div className="banner">
        <div className="banner-text">
          Altitude - Drone Vision 🚁
          <span> • </span>
          Altitude - Drone Vision 🚁
        </div>
      </div>

      <h2>🎥 Video Upload + Detection</h2>

      {/* UPLOAD */}
      <input type="file" accept="video/*" onChange={handleFileChange} />

      {preview && (
        <div style={{ marginTop: 20 }}>
          <video width="100%" controls src={preview} />
        </div>
      )}

      <button
        onClick={handleUpload}
        disabled={!file || uploading}
        style={{ marginTop: 20 }}
      >
        {uploading ? "Uploading..." : "Upload Video"}
      </button>

      {error && <p style={{ color: "red" }}>❌ {error}</p>}

      {success && (
        <div style={{ marginTop: 20 }}>
          <p style={{ color: "green" }}>✅ Upload successful</p>

          <button
            onClick={handleDelete}
            style={{
              marginTop: 10,
              background: "red",
              color: "white",
              padding: "8px 12px",
              border: "none",
              cursor: "pointer",
            }}
          >
            🗑 Delete Video
          </button>
        </div>
      )}

      {/* =========================
          DETECTION SECTION
      ========================= */}
      <hr style={{ margin: "40px 0" }} />

      <h2>🧠 Detection</h2>

      {!detecting ? (
        <button onClick={startDetect}>▶ Start Detection</button>
      ) : (
        <button onClick={stopDetect}>⏹ Stop Detection</button>
      )}

      <p>Status: {status}</p>

      {/* STREAM */}
      <div style={{ marginTop: 20 }}>
        {frame ? (
          <img
            src={`data:image/jpeg;base64,${frame}`}
            style={{ width: "100%", borderRadius: 10 }}
          />
        ) : (
          <p>No stream yet</p>
        )}
      </div>

      {/* DETECTIONS */}
      {detections.length > 0 && (
        <div style={{ marginTop: 10 }}>
          <h4>Detections</h4>
          <ul>
            {detections.map((d, i) => (
              <li key={i}>
                {d.label} ({Math.round(d.confidence * 100)}%)
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}