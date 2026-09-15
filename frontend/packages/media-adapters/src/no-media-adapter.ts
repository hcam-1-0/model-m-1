import type { MediaAdapter } from "./index";

export function createNoMediaAdapter(reason = "browser_unsupported"): MediaAdapter {
  return {
    transport: "none",
    attach() {
      return Promise.resolve({ state: "unsupported", reason });
    },
    teardown() {
      return undefined;
    },
  };
}
