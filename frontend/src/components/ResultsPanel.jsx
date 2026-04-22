import "./RollingBanner.css";

export default function RollingBanner({ text }) {
  return (
    <div className="rb-wrapper">
      <div className="rb-track">
        <span>{text}</span>
        <span>{text}</span>
        <span>{text}</span>
        <span>{text}</span>
      </div>
    </div>
  );
}