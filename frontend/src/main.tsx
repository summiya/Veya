import React from "react";
import ReactDOM from "react-dom/client";
import * as Sentry from "@sentry/react";
import { BrowserRouter } from "react-router-dom";

import App from "./App";
import { AppErrorFallback } from "./components/errors/AppErrorFallback";
import { AuthProvider } from "./context/AuthContext";
import { initializeFrontendMonitoring } from "./monitoring";
import "./styles.css";


initializeFrontendMonitoring();

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <Sentry.ErrorBoundary fallback={<AppErrorFallback />}>
      <BrowserRouter>
        <AuthProvider>
          <App />
        </AuthProvider>
      </BrowserRouter>
    </Sentry.ErrorBoundary>
  </React.StrictMode>,
);
