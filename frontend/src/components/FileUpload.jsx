import React from "react";

export default function FileUpload({ setFile }) {
  return (
    <div>
      <input
        type="file"
        accept="image/*,video/*"
        onChange={(e) => setFile(e.target.files[0])}
      />
    </div>
  );
}