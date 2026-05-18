import "./styles/banner.css";
import React, { useState, useRef, useEffect } from "react";

const API = import.meta.env.VITE_API_URL;

export default function App() {
  const [mode, setMode] = useState("upload"); // upload | camera

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

  const [fps, setFps] = useState(0);

  const readerRef = useRef(null);
  const fpsRef = useRef({ last: Date.now(), count: 0 });

  // =========================
  // RESET ON MODE CHANGE
  // =========================
  useEffect(() => {
    setFile(null);
    setPreview(null);
    setFrame(null);
    setDetections([]);
    setProgress(0);
    setStatus("idle");
    setError(null);
    setSuccess(false);
  }, [mode]);

  // =========================
  // FILE HANDLING
  // =========================
  const handleFileChange = (e) => {
    const f = e.target.files[0];

    if (!f) return;

    setFile(f);
    setPreview(URL.createObjectURL(f));
  };

  // =========================
  // UPLOAD
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

      if (!res.ok)
        throw new Error(data.detail || "Upload failed");

      setSuccess(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  // =========================
  // STREAM
  // =========================
  const startStream = async () => {
    setStatus("running");

    const cleanedPrompts = prompt
      .split(",")
      .map((p) => p.trim().toLowerCase())
      .filter(Boolean);

    try {
      await fetch(`${API}/api/set-prompts`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          prompts: cleanedPrompts,
        }),
      });
    } catch {}

    try {
      // =========================
      // SWITCH STREAM SOURCE
      // =========================
      const endpoint =
        mode === "camera"
          ? `${API}/api/camera-stream`
          : `${API}/api/video`;

      const res = await fetch(endpoint);

      if (!res.ok || !res.body)
        throw new Error("Stream failed");

      const reader = res.body.getReader();
      readerRef.current = reader;

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();

        if (done)
          throw new Error("Stream ended");

        buffer += decoder.decode(value, {
          stream: true,
        });

        const parts = buffer.split("\n");
        buffer = parts.pop();

        for (const part of parts) {
          if (!part.trim()) continue;

          let data;

          try {
            data = JSON.parse(part);
          } catch {
            continue;
          }

          if (data.image)
            setFrame(data.image);

          if (Array.isArray(data.detections))
            setDetections(data.detections);

          if (data.progress !== undefined)
            setProgress(data.progress);

          // =========================
          // FPS COUNTER
          // =========================
          fpsRef.current.count++;

          const now = Date.now();
          const diff = now - fpsRef.current.last;

          if (diff >= 1000) {
            setFps(
              Math.round(
                (fpsRef.current.count * 1000) / diff
              )
            );

            fpsRef.current.count = 0;
            fpsRef.current.last = now;
          }

          if (data.status === "done") {
            setStatus("done");
            return;
          }
        }
      }
    } catch (err) {
      console.warn(err.message);
      setStatus("error");
    }
  };

  // =========================
  // STOP
  // =========================
  const stopStream = async () => {
    setStatus("stopped");

    if (readerRef.current) {
      await readerRef.current.cancel();
    }
  };

  // =========================
  // UI
  // =========================
  return (
    <div
      style={{
        maxWidth: 800,
        margin: "auto",
        padding: 20,
      }}
    >
      <div className="banner">
        <div className="banner-text">
          Computer Vision - Video and Edge Device - AI Insight Analysis - Web Streaming  📹 
          • Computer Vision - Video and Edge Device - AI Insight Analysis - Web Streaming  📹
        </div>
      </div>

      {/* MODE */}
      <h2>Input Mode</h2>

      <button
        onClick={() => setMode("upload")}
      >
        📁 Upload Mode
      </button>

      <button
        onClick={() => setMode("camera")}
      >
        🎥 Camera Mode
      </button>

      <hr />

      {/* =========================
          UPLOAD MODE ONLY
      ========================= */}

      {mode === "upload" && (
        <>
          <h2>📁 Upload Video</h2>

          <input
            type="file"
            accept="video/*"
            onChange={handleFileChange}
          />

          <button
            onClick={handleUpload}
            disabled={uploading}
          >
            {uploading
              ? "Uploading..."
              : "Upload"}
          </button>

          {success && <p>✅ Uploaded</p>}

          {error && (
            <p style={{ color: "red" }}>
              {error}
            </p>
          )}
        </>
      )}

      {/* =========================
          PREVIEW
      ========================= */}

      <h3>📺 Input Preview</h3>

      {/* Upload Preview */}
      {mode === "upload" && preview && (
        <video
          width="100%"
          controls
          src={preview}
        />
      )}

      {/* Video File Preview */}
      {mode === "video" && (
        <img
          src={`${API}/api/video-preview`}
          style={{ width: "100%" }}
          alt="video-preview"
        />
      )}
      
      {/* Camera Preview */}
      {mode === "camera" && (
        <img
          src={`${API}/api/camera-preview`}
          style={{ width: "100%" }}
          alt="camera-preview"
        />
      )}

      <hr />

      {/* PROMPT */}
      <h2>
        🔎 Prompt (auto switches YOLO →
        YOLO-World)
      </h2>

      <input
        value={prompt}
        onChange={(e) =>
          setPrompt(e.target.value)
        }
        style={{
          width: "100%",
          padding: 10,
        }}
      />

      <hr />

      {/* DETECTION */}
      <h2>🧠 Detection</h2>

      <button onClick={startStream}>
        ▶ Start Stream
      </button>

      <button onClick={stopStream}>
        ⏹ Stop
      </button>

      <p>Status: {status}</p>

      <p>FPS: {fps}</p>

      <p>
        Progress: [
        <span style={{ color: "green" }}>
          {"█".repeat(
            Math.round(progress / 5)
          )}
        </span>
        <span style={{ color: "#ddd" }}>
          {"░".repeat(
            20 -
              Math.round(progress / 5)
          )}
        </span>
        ] {progress.toFixed(1)}%
      </p>

      {/* STREAM OUTPUT */}
      {frame ? (
        <img
          src={`data:image/jpeg;base64,${frame}`}
          style={{
            width: "100%",
            marginTop: 20,
          }}
          alt="stream-output"
        />
      ) : (
        <p>No stream yet</p>
      )}

      {/* DETECTIONS */}
      {detections.length > 0 ? (
        <ul>
          {detections.map((d, i) => (
            <li key={i}>
              {d.label} (
              {Math.round(
                d.confidence * 100
              )}
              %)
            </li>
          ))}
        </ul>
      ) : (
        <p style={{ opacity: 0.6 }}>
          No matching objects detected
        </p>
      )}
    </div>
  );
}



// import "./styles/banner.css";
// import React, { useState, useRef, useEffect } from "react";

// const API = import.meta.env.VITE_API_URL;

// export default function App() {
//   const [mode, setMode] = useState("upload"); // upload | camera

//   const [file, setFile] = useState(null);
//   const [preview, setPreview] = useState(null);

//   const [uploading, setUploading] = useState(false);
//   const [success, setSuccess] = useState(false);
//   const [error, setError] = useState(null);

//   const [frame, setFrame] = useState(null);
//   const [detections, setDetections] = useState([]);
//   const [status, setStatus] = useState("idle");

//   const [progress, setProgress] = useState(0);
//   const [prompt, setPrompt] = useState("person, car");

//   const [fps, setFps] = useState(0);

//   const readerRef = useRef(null);
//   const fpsRef = useRef({ last: Date.now(), count: 0 });

//   // =========================
//   // RESET ON MODE CHANGE
//   // =========================
//   useEffect(() => {
//     setFile(null);
//     setPreview(null);
//     setFrame(null);
//     setDetections([]);
//     setProgress(0);
//     setStatus("idle");
//     setError(null);
//     setSuccess(false);
//   }, [mode]);

//   // =========================
//   // FILE HANDLING
//   // =========================
//   const handleFileChange = (e) => {
//     const f = e.target.files[0];

//     if (!f) return;

//     setFile(f);
//     setPreview(URL.createObjectURL(f));
//   };

//   // =========================
//   // UPLOAD
//   // =========================
//   const handleUpload = async () => {
//     if (!file) return;

//     setUploading(true);
//     setError(null);

//     try {
//       const formData = new FormData();
//       formData.append("file", file);

//       const res = await fetch(`${API}/api/upload-video`, {
//         method: "POST",
//         body: formData,
//       });

//       const data = await res.json();

//       if (!res.ok)
//         throw new Error(data.detail || "Upload failed");

//       setSuccess(true);
//     } catch (err) {
//       setError(err.message);
//     } finally {
//       setUploading(false);
//     }
//   };

//   // =========================
//   // STREAM
//   // =========================
//   const startStream = async () => {
//     setStatus("running");

//     const cleanedPrompts = prompt
//       .split(",")
//       .map((p) => p.trim().toLowerCase())
//       .filter(Boolean);

//     try {
//       await fetch(`${API}/api/set-prompts`, {
//         method: "POST",
//         headers: {
//           "Content-Type": "application/json",
//         },
//         body: JSON.stringify({
//           prompts: cleanedPrompts,
//         }),
//       });
//     } catch {}

//     try {
//       // =========================
//       // SWITCH STREAM SOURCE
//       // =========================
//       const endpoint =
//         mode === "camera"
//           ? `${API}/api/camera-stream`
//           : `${API}/api/video`;

//       const res = await fetch(endpoint);

//       if (!res.ok || !res.body)
//         throw new Error("Stream failed");

//       const reader = res.body.getReader();
//       readerRef.current = reader;

//       const decoder = new TextDecoder();
//       let buffer = "";

//       while (true) {
//         const { value, done } = await reader.read();

//         if (done)
//           throw new Error("Stream ended");

//         buffer += decoder.decode(value, {
//           stream: true,
//         });

//         const parts = buffer.split("\n");
//         buffer = parts.pop();

//         for (const part of parts) {
//           if (!part.trim()) continue;

//           let data;

//           try {
//             data = JSON.parse(part);
//           } catch {
//             continue;
//           }

//           if (data.image)
//             setFrame(data.image);

//           if (Array.isArray(data.detections))
//             setDetections(data.detections);

//           if (data.progress !== undefined)
//             setProgress(data.progress);

//           // =========================
//           // FPS COUNTER
//           // =========================
//           fpsRef.current.count++;

//           const now = Date.now();
//           const diff = now - fpsRef.current.last;

//           if (diff >= 1000) {
//             setFps(
//               Math.round(
//                 (fpsRef.current.count * 1000) / diff
//               )
//             );

//             fpsRef.current.count = 0;
//             fpsRef.current.last = now;
//           }

//           if (data.status === "done") {
//             setStatus("done");
//             return;
//           }
//         }
//       }
//     } catch (err) {
//       console.warn(err.message);
//       setStatus("error");
//     }
//   };

//   // =========================
//   // STOP
//   // =========================
//   const stopStream = async () => {
//     setStatus("stopped");

//     if (readerRef.current) {
//       await readerRef.current.cancel();
//     }
//   };

//   // =========================
//   // UI
//   // =========================
//   return (
//     <div
//       style={{
//         maxWidth: 800,
//         margin: "auto",
//         padding: 20,
//       }}
//     >
//       <div className="banner">
//         <div className="banner-text">
//           Computer Vision - Video and Edge Device - AI Insight Analysis - Web Streaming  📹 
//           • Computer Vision - Video and Edge Device - AI Insight Analysis - Web Streaming  📹
//         </div>
//       </div>

//       {/* MODE */}
//       <h2>Input Mode</h2>

//       <button
//         onClick={() => setMode("upload")}
//       >
//         📁 Upload Mode
//       </button>

//       <button
//         onClick={() => setMode("camera")}
//       >
//         🎥 Camera Mode
//       </button>

//       <hr />

//       {/* =========================
//           UPLOAD MODE ONLY
//       ========================= */}

//       {mode === "upload" && (
//         <>
//           <h2>📁 Upload Video</h2>

//           <input
//             type="file"
//             accept="video/*"
//             onChange={handleFileChange}
//           />

//           <button
//             onClick={handleUpload}
//             disabled={uploading}
//           >
//             {uploading
//               ? "Uploading..."
//               : "Upload"}
//           </button>

//           {success && <p>✅ Uploaded</p>}

//           {error && (
//             <p style={{ color: "red" }}>
//               {error}
//             </p>
//           )}
//         </>
//       )}

//       {/* =========================
//           PREVIEW
//       ========================= */}

//       <h3>📺 Input Preview</h3>

//       {/* Upload Preview */}
//       {mode === "upload" && preview && (
//         <video
//           width="100%"
//           controls
//           src={preview}
//         />
//       )}

//       {/* Video File Preview */}
//       {mode === "video" && (
//         <img
//           src={`${API}/api/video-preview`}
//           style={{ width: "100%" }}
//           alt="video-preview"
//         />
//       )}
      
//       {/* Camera Preview */}
//       {mode === "camera" && (
//         <img
//           src={`${API}/api/camera-preview`}
//           style={{ width: "100%" }}
//           alt="camera-preview"
//         />
//       )}

//       <hr />

//       {/* PROMPT */}
//       <h2>
//         🔎 Prompt (auto switches YOLO →
//         YOLO-World)
//       </h2>

//       <input
//         value={prompt}
//         onChange={(e) =>
//           setPrompt(e.target.value)
//         }
//         style={{
//           width: "100%",
//           padding: 10,
//         }}
//       />

//       <hr />

//       {/* DETECTION */}
//       <h2>🧠 Detection</h2>

//       <button onClick={startStream}>
//         ▶ Start Stream
//       </button>

//       <button onClick={stopStream}>
//         ⏹ Stop
//       </button>

//       <p>Status: {status}</p>

//       <p>FPS: {fps}</p>

//       <p>
//         Progress: [
//         <span style={{ color: "green" }}>
//           {"█".repeat(
//             Math.round(progress / 5)
//           )}
//         </span>
//         <span style={{ color: "#ddd" }}>
//           {"░".repeat(
//             20 -
//               Math.round(progress / 5)
//           )}
//         </span>
//         ] {progress.toFixed(1)}%
//       </p>

//       {/* STREAM OUTPUT */}
//       {frame ? (
//         <img
//           src={`data:image/jpeg;base64,${frame}`}
//           style={{
//             width: "100%",
//             marginTop: 20,
//           }}
//           alt="stream-output"
//         />
//       ) : (
//         <p>No stream yet</p>
//       )}

//       {/* DETECTIONS */}
//       {detections.length > 0 ? (
//         <ul>
//           {detections.map((d, i) => (
//             <li key={i}>
//               {d.label} (
//               {Math.round(
//                 d.confidence * 100
//               )}
//               %)
//             </li>
//           ))}
//         </ul>
//       ) : (
//         <p style={{ opacity: 0.6 }}>
//           No matching objects detected
//         </p>
//       )}
//     </div>
//   );
// }

