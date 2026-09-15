import type { Meta, StoryObj } from "@storybook/react-vite";
import { Button, Disclosure, SelectField, StateBanner, TextField } from "./index";
const meta = {
  title: "Foundation/Primitives",
  component: StateBanner,
  parameters: { layout: "padded" },
  tags: ["autodocs"],
} satisfies Meta<typeof StateBanner>;
export default meta;
type Story = StoryObj<typeof meta>;
export const Ready: Story = {
  args: { state: "ready", title: "Workspace is current", detail: "Generated state only." },
};
export const Degraded: Story = {
  args: {
    state: "degraded",
    title: "Optional visual features are unavailable",
    detail: "The complete list workflow remains available.",
    action: <Button>View list</Button>,
  },
};
export const Form: Story = {
  args: { state: "ready", title: "Generated form" },
  render: () => (
    <div style={{ display: "grid", gap: 16, maxWidth: 420 }}>
      <TextField label="Generated reference" placeholder="SYN-REFERENCE" />
      <SelectField label="Status">
        <option>Ready</option>
        <option>Degraded</option>
      </SelectField>
      <Disclosure summary="Details">Generated foundation details.</Disclosure>
    </div>
  ),
};
