import { StrictMode, useEffect } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import "katex/dist/katex.min.css";
import { App } from "./App";
import { api } from "./api";
import { AuthProvider } from "./auth";
import "./styles.css";

function Root() {
  useEffect(() => {
    api
      .settings()
      .then((settings) => {
        const theme =
          settings.theme === "system"
            ? window.matchMedia("(prefers-color-scheme: dark)").matches
              ? "dark"
              : "light"
            : settings.theme;
        document.documentElement.dataset.theme = theme;
      })
      .catch(() => {
        document.documentElement.dataset.theme = window.matchMedia("(prefers-color-scheme: dark)").matches
          ? "dark"
          : "light";
      });
  }, []);

  return (
    <BrowserRouter>
      <AuthProvider>
        <App />
      </AuthProvider>
    </BrowserRouter>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <Root />
  </StrictMode>,
);
