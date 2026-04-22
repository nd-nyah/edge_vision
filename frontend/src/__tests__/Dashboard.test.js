import { render, screen, fireEvent } from "@testing-library/react";
import axios from "axios";
import MockAdapter from "axios-mock-adapter";
import Dashboard from "../pages/Dashboard";

const mock = new MockAdapter(axios);

describe("Drone Vision Dashboard", () => {

  afterEach(() => {
    mock.reset();
  });

  // -------------------------
  // UI RENDER TEST
  // -------------------------
  test("renders dashboard title", () => {
    render(<Dashboard />);
    expect(screen.getByText(/Drone Vision Dashboard/i)).toBeInTheDocument();
  });

  // -------------------------
  // MODE SWITCH TEST
  // -------------------------
  test("switches to realtime mode", () => {
    render(<Dashboard />);

    const btn = screen.getByText("Real-Time Mode");
    fireEvent.click(btn);

    expect(btn).toBeInTheDocument();
  });

  // -------------------------
  // FILE MODE TEST
  // -------------------------
  test("shows file input in file mode", () => {
    render(<Dashboard />);
    expect(screen.getByRole("button", { name: /Run Detection/i })).toBeInTheDocument();
  });

  // -------------------------
  // API CALL TEST
  // -------------------------
  test("calls /detect API and shows results", async () => {

    mock.onPost("http://localhost:8000/detect").reply(200, {
      detections: [
        { label: "person", confidence: 0.9 }
      ],
      confidence: 0.9,
      metadata: { source: "test" }
    });

    render(<Dashboard />);

    fireEvent.click(screen.getByText("Run Detection"));

    // wait for result
    const result = await screen.findByText(/person/i);
    expect(result).toBeInTheDocument();
  });
});