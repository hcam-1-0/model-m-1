import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router";
import { CameraCataloguePage } from "../apps/operations-center/src/pages/camera-catalogue-page";

afterEach(cleanup);
describe("camera catalogue", () => {
  it("renders a generated authoritative table", () => {
    render(
      <MemoryRouter>
        <CameraCataloguePage />
      </MemoryRouter>,
    );
    expect(screen.getByRole("heading", { name: "Camera catalogue" })).toBeInTheDocument();
    expect(screen.getByText("Generated camera 0001")).toBeInTheDocument();
    expect(screen.getAllByRole("row")).toHaveLength(11);
  });
  it("filters without hiding the authoritative empty state", () => {
    render(
      <MemoryRouter>
        <CameraCataloguePage />
      </MemoryRouter>,
    );
    fireEvent.change(screen.getByLabelText("Find camera"), { target: { value: "does not exist" } });
    expect(screen.getByText("No generated cameras match")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Clear filters" }));
    expect(screen.getByText("Generated camera 0001")).toBeInTheDocument();
  });
});
