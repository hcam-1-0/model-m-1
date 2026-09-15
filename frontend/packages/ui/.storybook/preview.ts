import type { Preview } from "@storybook/react-vite";
import "@hcam/design-tokens/styles.css";
import "../../app-shell/src/styles.css";
const preview: Preview = {
  parameters: {
    a11y: { test: "error" },
    backgrounds: { disable: true },
    controls: { expanded: true },
  },
};
export default preview;
