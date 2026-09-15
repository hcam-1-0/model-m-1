import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import {
  NavigationSection,
  PortalSwitcher,
  RouteGlyph,
  WorkspaceCommandPalette,
} from "../packages/ui/src";

afterEach(cleanup);

describe("shared portal navigation", () => {
  it("presents all workspaces in a grouped, current-aware switcher", () => {
    const { container } = render(<PortalSwitcher current="command" />);
    const switcher = container.querySelector("details");
    const summary = screen.getByLabelText("Switch workspace. Current workspace: Command Center");

    fireEvent.click(summary);
    expect(switcher).toHaveAttribute("open");
    expect(screen.getAllByRole("link")).toHaveLength(8);
    expect(screen.getByRole("link", { name: /Command Center/ })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(screen.getByRole("link", { name: /GIS Center/ })).toHaveAttribute(
      "href",
      "http://localhost:4174/gis",
    );

    fireEvent.keyDown(document, { key: "Escape" });
    expect(switcher).not.toHaveAttribute("open");

    fireEvent.keyDown(document, { key: "w", altKey: true });
    expect(switcher).toHaveAttribute("open");
    expect(screen.getByRole("link", { name: /Command Center/ })).toHaveFocus();
  });

  it("exposes semantic navigation groups and route glyphs", () => {
    render(
      <nav aria-label="Test navigation">
        <NavigationSection label="Situation">
          <a href="/command/live">
            <RouteGlyph path="/command/live" />
            <span>Live situation</span>
          </a>
        </NavigationSection>
      </nav>,
    );

    expect(screen.getByRole("group", { name: "Situation" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Live situation" })).toBeInTheDocument();
    expect(screen.getByText("1")).toBeInTheDocument();
    fireEvent.click(screen.getByText("Situation"));
    expect(screen.getByRole("group", { name: "Situation" })).not.toHaveAttribute("open");
  });

  it("filters command-palette destinations without losing its empty state", () => {
    render(
      <WorkspaceCommandPalette
        title="Command navigation"
        placeholder="Search views"
        boundary="Generated routes only."
        items={[
          { label: "Overview", href: "/command", group: "Situation" },
          { label: "Camera network", href: "/command/cameras", group: "Situation" },
          { label: "Platform health", href: "/command/health", group: "Platform" },
        ]}
        onClose={() => undefined}
      />,
    );

    const search = screen.getByRole("searchbox", { name: "Filter available routes" });
    expect(screen.getAllByRole("link")).toHaveLength(10);
    expect(screen.getByRole("link", { name: "GIS Center" })).toHaveAttribute(
      "href",
      "http://localhost:4174/gis",
    );
    expect(screen.getByRole("button", { name: "Close workspace search" })).toBeInTheDocument();
    fireEvent.keyDown(search, { key: "ArrowDown" });
    expect(screen.getByRole("link", { name: "Overview" })).toHaveFocus();
    fireEvent.keyDown(screen.getByRole("link", { name: "Overview" }), { key: "End" });
    expect(screen.getByRole("link", { name: "Security Center" })).toHaveFocus();
    fireEvent.change(search, { target: { value: "camera" } });
    expect(screen.getByRole("link", { name: "Camera network" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Overview" })).not.toBeInTheDocument();

    fireEvent.change(search, { target: { value: "not available" } });
    expect(screen.getByText("No matching views")).toBeInTheDocument();
  });
});
