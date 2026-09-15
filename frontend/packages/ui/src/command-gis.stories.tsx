import type { Meta, StoryObj } from "@storybook/react-vite";
import { Metric, StateBanner } from "./index";

const meta = {
  title: "Phase 5/Command and GIS states",
  component: StateBanner,
  parameters: { layout: "padded" },
  tags: ["autodocs"],
} satisfies Meta<typeof StateBanner>;
export default meta;
type Story = StoryObj<typeof meta>;
export const PartialSource: Story = {
  args: {
    state: "partial",
    title: "Generated source is partial",
    detail: "Fourteen producer gaps remain unavailable.",
  },
};
export const RendererDegraded: Story = {
  args: {
    state: "degraded",
    title: "Map renderer downgraded",
    detail: "The authoritative list and detail workflow remains complete.",
  },
};
export const UnknownTruth: Story = {
  args: {
    state: "unknown",
    title: "Authoritative state is unknown",
    detail: "No client-side conclusion is substituted.",
  },
};
export const SummaryMetrics: Story = {
  args: { state: "ready", title: "Generated Command summary" },
  render: () => (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(3, minmax(120px, 1fr))",
        gap: 8,
        maxWidth: 720,
      }}
    >
      <Metric label="Source projections" value="10" status="good" />
      <Metric label="Awaiting review" value="3" status="warning" />
      <Metric label="Producer gaps" value="14" />
    </div>
  ),
};
