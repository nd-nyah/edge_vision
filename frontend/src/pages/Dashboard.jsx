const handleRun = async () => {
  if (!file) return;

  setLoading(true);

  try {
    // 1️⃣ upload first
    const formData = new FormData();
    formData.append("file", file);

    const uploadRes = await fetch("http://localhost:8000/upload-video", {
      method: "POST",
      body: formData,
    });

    const uploadData = await uploadRes.json();

    // 2️⃣ then run detection
    const detectRes = await fetch("http://localhost:8000/start-detect", {
      method: "POST",
    });

    const detectData = await detectRes.json();

    setResult(detectData);

  } catch (err) {
    console.error(err);
  } finally {
    setLoading(false);
  }
};