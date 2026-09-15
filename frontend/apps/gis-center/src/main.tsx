import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router";
import { App } from "./app";
import "@hcam/design-tokens/styles.css";
import "maplibre-gl/dist/maplibre-gl.css";
import "./styles.css";
import "./operations.css";
import "@hcam/design-tokens/portal-polish.css";
const root = document.querySelector<HTMLElement>("#root");
if (!root) throw new Error("missing_application_root");
createRoot(root).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>,
);
