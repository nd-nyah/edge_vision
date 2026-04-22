import React from "react";

export default function RunButton({ onClick, loading }) {
  return (
    <button
      onClick={onClick}
      style={{
        marginTop: 20,
        padding: "10px 20px",
        background: "green",
        color: "white",
      }}
    >
      {loading ? "Processing..." : "Run Detection"}
    </button>
  );
}