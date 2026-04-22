import React, { useState } from "react";

const API = import.meta.env.VITE_API_BASE_URL;

export default function App() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  const [uploadedFileName, setUploadedFileName] = useState(null);

  const [frame, setFrame] = useState(null);
  const [detections, setDetections] = useState([]);
  const [status, setStatus] = useState("idle");
  const [detecting, setDetecting] = useState(false);

  // 📥 select file
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

  // 📤 upload
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

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Upload failed");
      }

      // ✅ FIX: use backend filename
      setUploadedFileName(data.filename);

      setSuccess(true);

    } catch (err) {
      console.error(err);
      setError(err.message || "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  // 🗑 delete video
  const handleDelete = async () => {
    if (!uploadedFileName) return;

    try {
      const res = await fetch(
        `${API}/delete-video?filename=${uploadedFileName}`,
        { method: "DELETE" }
      );

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.message || "Delete failed");
      }

      // FULL RESET
      setFile(null);
      setPreview(null);
      setUploadedFileName(null);
      setSuccess(false);
      setError(null);

      document.querySelector("input[type='file']").value = "";

      alert("Video deleted successfully 🗑");

    } catch (err) {
      console.error(err);
      alert("Delete failed ❌");
    }
  };

  // 🧠 detection controls
  const startDetect = async () => {
    await fetch(`${API}/start-detect`, { method: "POST" });
    setDetecting(true);
  };

  const stopDetect = async () => {
    await fetch(`${API}/stop-detect`, { method: "POST" });
    setDetecting(false);
  };

  return (
    <div style={{ maxWidth: 800, margin: "auto", padding: 20 }}>
      <h2>🎥 Video Upload UI</h2>

      {/* INPUT */}
      <input type="file" accept="video/*" onChange={handleFileChange} />

      {/* PREVIEW */}
      {preview && (
        <div style={{ marginTop: 20 }}>
          <h4>Preview</h4>
          <video width="100%" controls src={preview} />
        </div>
      )}

      {/* UPLOAD */}
      <button
        onClick={handleUpload}
        disabled={!file || uploading}
        style={{ marginTop: 20 }}
      >
        {uploading ? "Uploading..." : "Upload Video"}
      </button>

      {/* ERROR */}
      {error && <p style={{ color: "red" }}>❌ {error}</p>}

      {/* SUCCESS */}
      {success && (
        <div style={{ marginTop: 20 }}>
          <p style={{ color: "green" }}>✅ Upload successful</p>

          <button
            onClick={handleDelete}
            style={{
              marginTop: 10,
              padding: "8px 12px",
              background: "red",
              color: "white",
              border: "none",
              cursor: "pointer",
            }}
          >
            🗑 Delete Video
          </button>
        </div>
      )}

      {/* DETECTOR */}
      <hr style={{ margin: "40px 0" }} />

      <h2>🧠 Object Detection</h2>

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