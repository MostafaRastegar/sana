import React from "react";
import ReactDOM from "react-dom/client";
import { ConfigProvider, theme } from "antd";
import { RouterProvider } from "react-router-dom";
import { router } from "./App";
import { useUIStore } from "./store/uiStore";
import "./index.css";

function ThemedApp() {
  const uiTheme = useUIStore((s) => s.theme);

  return (
    <ConfigProvider
      theme={{
        algorithm: uiTheme === "dark" ? theme.darkAlgorithm : theme.defaultAlgorithm,
        token: {
          colorPrimary: "#1677ff",
          borderRadius: 6,
        },
      }}
    >
      <RouterProvider router={router} />
    </ConfigProvider>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ThemedApp />
  </React.StrictMode>
);