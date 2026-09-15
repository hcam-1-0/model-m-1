import type { Meta, StoryObj } from "@storybook/react-vite";
import { portals } from "@hcam/navigation";
import { PortalShellPreview } from "./index";
const meta = {
  title: "Foundation/Application shell",
  component: PortalShellPreview,
  parameters: { layout: "fullscreen" },
  args: { config: { portal: portals[0]! } },
} satisfies Meta<typeof PortalShellPreview>;
export default meta;
type Story = StoryObj<typeof meta>;
export const Desktop: Story = {};
export const Gujarati: Story = { args: { locale: "gu" } };
export const Stale: Story = { args: { config: { portal: portals[0]!, initialState: "stale" } } };
