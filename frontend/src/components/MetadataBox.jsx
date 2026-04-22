import React from "react";

export default function MetadataBox({ metadata }) {
  if (!metadata) return null;

  return (
    <div style={{ marginTop: 20 }}>
      <h3>Metadata</h3>
      <pre style={{ background: "#f4f4f4", padding: 10 }}>
        {JSON.stringify(metadata, null, 2)}
      </pre>
    </div>
  );
}