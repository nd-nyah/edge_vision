export const startDetect = () =>
  fetch("http://localhost:8000/start-detect", { method: "POST" });

export const stopDetect = () =>
  fetch("http://localhost:8000/stop-detect", { method: "POST" });