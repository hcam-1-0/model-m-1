import type { Meta, StoryObj } from "@storybook/react-vite";
import { StateBanner } from "./index";
const meta = {
  title: "P5.4/Intelligence review states",
  component: StateBanner,
  args: {
    state: "correction",
    title: "Correction requires authoritative refresh",
    detail: "Mutation remains disabled until HTTP confirms current state.",
  },
} satisfies Meta<typeof StateBanner>;
export default meta;
type Story = StoryObj<typeof meta>;
export const CorrectionHold: Story = {};
export const Conflict: Story = {
  args: {
    state: "conflict",
    title: "Server state changed",
    detail: "Compare current revision and explicitly reconsider. No automatic retry.",
  },
};
export const Denied: Story = {
  args: {
    state: "denied",
    title: "Review capability denied",
    detail: "No client override is available.",
  },
};
