import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import axe from "axe-core";
import { afterEach, describe, expect, it, vi } from "vitest";
import { portals } from "@hcam/navigation";
import { createPortalApp, PortalShellPreview } from "@hcam/app-shell";
import {
  Button,
  Disclosure,
  Metric,
  ModalDialog,
  SelectField,
  StateBanner,
  TextField,
  VisuallyHidden,
} from "@hcam/ui";
import { generatedStates } from "@hcam/test-fixtures";

afterEach(() => {
  cleanup();
  document.documentElement.removeAttribute("data-theme");
});
describe("application shell", () => {
  it("renders landmarks, labels, generated status, and no critical axe violations", async () => {
    const { container } = render(<PortalShellPreview config={{ portal: portals[0]! }} />);
    expect(screen.getByRole("heading", { level: 1, name: "Command Center" })).toBeVisible();
    expect(screen.getByRole("navigation", { name: "Primary navigation" })).toBeVisible();
    expect(screen.getByText("Generated environment. No operational data.")).toBeVisible();
    expect(screen.getByRole("main")).toHaveAttribute("id", "main-content");
    const report = await axe.run(container, { rules: { "color-contrast": { enabled: false } } });
    expect(report.violations).toEqual([]);
  });
  it("opens a focus-managed command dialog and closes with Escape", async () => {
    const user = userEvent.setup();
    render(<PortalShellPreview config={{ portal: portals[0]! }} />);
    await user.click(screen.getByRole("button", { name: "Open command search" }));
    expect(screen.getByRole("dialog", { name: "Command search" })).toBeVisible();
    expect(screen.getByRole("searchbox", { name: "Search available routes" })).toHaveFocus();
    fireEvent.keyDown(window, { key: "Escape" });
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });
  it("supports the command shortcut and a harmless theme preference", async () => {
    const user = userEvent.setup();
    render(<PortalShellPreview config={{ portal: portals[0]! }} />);
    fireEvent.keyDown(window, { key: "k", ctrlKey: true });
    expect(screen.getByRole("dialog", { name: "Command search" })).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Close command search" }));
    await user.click(screen.getByRole("button", { name: "Change theme" }));
    expect(document.documentElement.dataset.theme).toBe("dark");
    await user.click(screen.getByRole("button", { name: "Change theme" }));
    expect(document.documentElement.dataset.theme).toBe("light");
  });
  it("toggles compact navigation and closes it after route selection", async () => {
    const user = userEvent.setup();
    render(<PortalShellPreview config={{ portal: portals[0]! }} />);
    const menu = screen.getByRole("button", { name: "Open navigation" });
    await user.click(menu);
    expect(menu).toHaveAttribute("aria-expanded", "true");
    const activeLink = screen.getByRole("link", { name: "Command Center" });
    activeLink.addEventListener("click", (event) => event.preventDefault(), { once: true });
    fireEvent.click(activeLink);
    expect(menu).toHaveAttribute("aria-expanded", "false");
  });
  it("mounts and unmounts the standalone portal lifecycle", () => {
    const root = document.createElement("div");
    document.body.append(root);
    let dispose: () => void = () => undefined;
    act(() => {
      dispose = createPortalApp(root, { portal: portals[0]! });
    });
    expect(root.querySelector(".hcam-app-shell")).not.toBeNull();
    act(() => dispose());
    expect(root.childElementCount).toBe(0);
    root.remove();
  });
  it.each(generatedStates)("renders the %s state visibly", (state) => {
    render(<PortalShellPreview config={{ portal: portals[0]!, initialState: state }} />);
    expect(document.querySelector(`.hcam-state--${state}`)).toBeInTheDocument();
  });
  it("renders Gujarati and Hindi catalogues", () => {
    const { rerender } = render(
      <PortalShellPreview config={{ portal: portals[0]! }} locale="gu" />,
    );
    expect(screen.getByRole("heading", { level: 1, name: "કમાન્ડ સેન્ટર" })).toBeVisible();
    rerender(<PortalShellPreview config={{ portal: portals[0]! }} locale="hi" />);
    expect(screen.getByRole("heading", { level: 1, name: "कमांड सेंटर" })).toBeVisible();
  });
});

describe("accessible primitives", () => {
  it("provides native names, validation, selection, disclosure, and status semantics", async () => {
    const user = userEvent.setup();
    render(
      <>
        <TextField label="Generated reference" error="A generated value is required" />
        <SelectField label="Generated status">
          <option>Ready</option>
        </SelectField>
        <Disclosure summary="Generated details">
          <p>Bounded detail</p>
        </Disclosure>
        <StateBanner state="failure" title="Safe failure" action={<Button>Refresh</Button>} />
      </>,
    );
    expect(screen.getByRole("textbox", { name: "Generated reference" })).toHaveAttribute(
      "aria-invalid",
      "true",
    );
    expect(screen.getByRole("combobox", { name: "Generated status" })).toBeVisible();
    await user.click(screen.getByText("Generated details"));
    expect(screen.getByText("Bounded detail")).toBeVisible();
    expect(screen.getByRole("alert")).toHaveTextContent("A generated value is required");
    expect(screen.getByRole("button", { name: "Refresh" })).toBeVisible();
  });
  it("covers variants, optional content, and modal dismissal", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    render(
      <>
        <Button variant="primary">Primary</Button>
        <Button variant="danger">Danger</Button>
        <Metric label="Queue" value="4" status="warning" />
        <VisuallyHidden>Hidden context</VisuallyHidden>
        <TextField label="Optional field" />
        <StateBanner state="empty" title="Empty" />
        <ModalDialog title="Generated modal" onClose={onClose}>
          <button type="button">Inside</button>
        </ModalDialog>
      </>,
    );
    expect(screen.getByText("Hidden context")).toHaveClass("hcam-visually-hidden");
    expect(screen.getByRole("textbox", { name: "Optional field" })).not.toHaveAttribute(
      "aria-invalid",
    );
    const dialog = screen.getByRole("dialog", { name: "Generated modal" });
    await user.click(dialog);
    fireEvent(dialog, new Event("cancel", { cancelable: true }));
    expect(onClose).toHaveBeenCalled();
  });
});
