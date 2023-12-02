import React from "react";
import ReactDOM from "react-dom/client";
import type { ErrorPayload } from "vite";
import App from "./App";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// REGISTER ERROR OVERLAY for vite dev server
const showErrorOverlay = (err: Partial<ErrorPayload["err"]>) => {
  // must be within function call because that's when the element is defined for sure.
  const ErrorOverlay = customElements.get("vite-error-overlay");
  // don't open outside vite environment
  if (!ErrorOverlay) {
    return;
  }
  console.log(err);
  const overlay = new ErrorOverlay(err);
  document.body.appendChild(overlay);
};

window.addEventListener("error", (error) => showErrorOverlay(error.error));
window.addEventListener("unhandledrejection", (error) =>
  showErrorOverlay(error.reason)
);
