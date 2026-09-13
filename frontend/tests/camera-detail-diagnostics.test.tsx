import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router";
import { CameraDetailPage } from "../apps/operations-center/src/pages/camera-detail-page";
import { StreamDiagnosticsPage } from "../apps/operations-center/src/pages/stream-diagnostics-page";

afterEach(cleanup);
describe("camera detail and diagnostics", () => {
  it("shows sanitized capability and generated probe truth", () => {
    render(
      <MemoryRouter initialEntries={["/operations/cameras/SYN-CAM-0001"]}>
        <Routes>
          <Route path="/operations/cameras/:cameraId" element={<CameraDetailPage />} />
        </Routes>
      </MemoryRouter>,
    );
    expect(screen.getByRole("heading", { name: "Generated camera 0001" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Stream capability" })).toBeInTheDocument();
    expect(screen.getByText("Metadata probe completed")).toBeInTheDocument();
    expect(document.body.textContent).not.toMatch(/rtsp:|password|secret_ref/i);
  });
  it("keeps prohibited controls visibly disabled by policy", () => {
    render(
      <MemoryRouter initialEntries={["/operations/diagnostics/SYN-STREAM-0001"]}>
        <Routes>
          <Route path="/operations/diagnostics/:streamId" element={<StreamDiagnosticsPage />} />
        </Routes>
      </MemoryRouter>,
    );
    expect(screen.getByText("Zero media retention")).toBeInTheDocument();
    expect(screen.getByText("PTZ and control")).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /record|snapshot|download|ptz/i }),
    ).not.toBeInTheDocument();
  });
});
