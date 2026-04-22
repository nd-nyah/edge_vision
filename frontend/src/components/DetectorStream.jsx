import React from "react";
import useWebSocket from "../hooks/useWebSocket";
import { startDetect, stopDetect } from "../services/detectorApi";

export default function DetectorStream() {
  const { frame, detections, status } = useWebSocket(
    "ws://localhost:8000/ws/stream"
  );

  return (
    <div style={{ marginTop: 40 }}>
      <h3>🧠 Object Detector</h3>

      {/* video stream */}
      {frame ? (
        <img
          src={`data:image/jpeg;base64,${frame}`}
          alt="stream"
          style={{ width: "100%", borderRadius: 8 }}
        />
      ) : (
        <p>No video stream</p>
      )}

      {/* status */}
      <p>Status: {status}</p>

      {/* controls */}
      <div style={{ marginTop: 10 }}>
        <button onClick={startDetect}>▶ Start</button>
        <button onClick={stopDetect} style={{ marginLeft: 10 }}>
          ⏹ Stop
        </button>
      </div>

      {/* detections */}
      {detections.length > 0 && (
        <div style={{ marginTop: 15 }}>
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