import { useEffect, useState } from "react";

export default function useWebSocket(url) {
  const [frame, setFrame] = useState(null);
  const [detections, setDetections] = useState([]);
  const [status, setStatus] = useState("idle");

  useEffect(() => {
    const ws = new WebSocket(url);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      setFrame(data.frame);
      setDetections(data.detections);
      setStatus(data.status);
    };

    ws.onerror = (err) => {
      console.error("WebSocket error:", err);
    };

    return () => ws.close();
  }, [url]);

  return { frame, detections, status };
}