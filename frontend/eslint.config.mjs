import eslint from "@eslint/js";
import reactHooks from "eslint-plugin-react-hooks";
import tseslint from "typescript-eslint";

const browserGlobals = Object.fromEntries(
  [
    "AbortController",
    "CustomEvent",
    "Document",
    "Element",
    "Event",
    "HTMLElement",
    "IntersectionObserver",
    "KeyboardEvent",
    "Location",
    "MediaQueryList",
    "MutationObserver",
    "Navigator",
    "Node",
    "Performance",
    "Request",
    "Response",
    "Storage",
    "URL",
    "URLSearchParams",
    "WebSocket",
    "Window",
    "clearInterval",
    "clearTimeout",
    "console",
    "crypto",
    "document",
    "fetch",
    "globalThis",
    "history",
    "localStorage",
    "location",
    "navigator",
    "performance",
    "queueMicrotask",
    "requestAnimationFrame",
    "sessionStorage",
    "setInterval",
    "setTimeout",
    "window",
  ].map((name) => [name, "readonly"]),
);

export default tseslint.config(
  {
    ignores: [
      "**/dist/**",
      "**/coverage/**",
      "**/node_modules/**",
      "**/storybook-static/**",
      "**/playwright-report/**",
      "**/test-results/**",
      "dependency-lock-candidate.json",
      "dependency-evidence.json",
      "sbom.cdx.json",
    ],
  },
  eslint.configs.recommended,
  ...tseslint.configs.strictTypeChecked,
  ...tseslint.configs.stylisticTypeChecked,
  {
    files: ["**/*.{ts,tsx}"],
    languageOptions: {
      globals: browserGlobals,
      parserOptions: {
        projectService: { allowDefaultProject: ["*.ts"] },
        tsconfigRootDir: import.meta.dirname,
      },
    },
    plugins: {
      "react-hooks": reactHooks,
    },
    rules: {
      ...reactHooks.configs.flat.recommended.rules,
      "@typescript-eslint/consistent-type-imports": "error",
      "@typescript-eslint/no-confusing-void-expression": "off",
      "@typescript-eslint/no-misused-promises": ["error", { checksVoidReturn: false }],
      "@typescript-eslint/restrict-template-expressions": ["error", { allowNumber: true }],
    },
  },
  {
    files: ["**/*.test.{ts,tsx}", "**/*.spec.ts", "**/*.stories.tsx"],
    rules: { "@typescript-eslint/no-non-null-assertion": "off" },
  },
  {
    files: ["*.ts", "**/.storybook/*.ts", "**/*.stories.tsx"],
    ...tseslint.configs.disableTypeChecked,
  },
  {
    files: ["**/*.{js,mjs}"],
    ...tseslint.configs.disableTypeChecked,
    languageOptions: {
      globals: {
        console: "readonly",
        process: "readonly",
        Buffer: "readonly",
        URL: "readonly",
        crypto: "readonly",
      },
    },
  },
);
