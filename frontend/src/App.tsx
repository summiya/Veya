import { Navigate, Route, Routes } from "react-router-dom";

import { ProtectedRoute } from "./components/auth/ProtectedRoute";
import { DashboardPage } from "./pages/DashboardPage";
import { ForgotPasswordPage } from "./pages/ForgotPasswordPage";
import { LoginPage } from "./pages/LoginPage";
import { SignupPage } from "./pages/SignupPage";

export default function App() {
  return (
    <Routes>
      <Route element={<Navigate replace to="/login" />} path="/" />
      <Route element={<LoginPage />} path="/login" />
      <Route element={<SignupPage />} path="/signup" />
      <Route element={<ForgotPasswordPage />} path="/forgot-password" />

      <Route element={<ProtectedRoute />}>
        <Route element={<DashboardPage />} path="/dashboard" />
      </Route>

      <Route element={<Navigate replace to="/" />} path="*" />
    </Routes>
  );
}
