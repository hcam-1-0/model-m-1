import type { Meta, StoryObj } from "@storybook/react-vite";
import { Metric, StateBanner } from "./index";

const meta = {
  title: "Phase 5/Camera and live states",
  component: StateBanner,
  parameters: { layout: "padded" },
  tags: ["autodocs"],
} satisfies Meta<typeof StateBanner>;
export default meta;
type Story = StoryObj<typeof meta>;

export const StreamStalled: Story = {
  args: {
    state: "degraded",
    title: "Generated stream stalled",
    detail: "Bounded recovery is active; the authoritative camera status remains available.",
  },
};
export const GrantExpired: Story = {
  args: {
    state: "stale",
    title: "Playback grant expired",
    detail: "The generated session was released and no media locator was retained.",
  },
};
export const BrowserUnsupported: Story = {
  args: {
    state: "unsupported",
    title: "Video unavailable in this browser",
    detail: "Camera identity, health, diagnostics, and handoff controls remain complete.",
  },
};
export const AdmissionSummary: Story = {
  args: { state: "ready", title: "Generated live workspace" },
  render: () => (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(3, minmax(120px, 1fr))",
        gap: 8,
        maxWidth: 720,
      }}
    >
      <Metric label="Requested" value="10" />
      <Metric label="Admitted" value="4" status="good" />
      <Metric label="Held by budget" value="6" status="warning" />
    </div>
  ),
};
