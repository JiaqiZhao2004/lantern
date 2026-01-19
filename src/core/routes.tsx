// src/app/routes.tsx
import React, { useContext, useEffect } from "react";
import { Navigate, Route, Routes, useNavigate } from "react-router-dom";

import LoginPage from "../features/auth/pages/LoginPage";
import DashboardPage from "../features/dashboard/pages/DashboardPage";

import RegisterPage from "../features/auth/pages/RegisterPage";
// import MFAPage from "../features/auth/pages/MFAPage";
import EmailVerificationPage from "../features/auth/pages/EmailVerificationPage";
import { AuthContext } from "../features/auth/state/AuthContext";
// import MFASetupPage from "../features/auth/pages/MFASetupPage";
// import MFAVerifyPage from "../features/auth/pages/MFAVerifyPage";

export function AppRoutes() {
  const authctx = useContext(AuthContext);
  const navigate = useNavigate();

  // All auth routing is based on AuthContext
  useEffect(() => {
    if (!authctx?.state.user) {
      if (window.location.pathname === "/register") {
        return;
      }
      navigate("/login");
    } else if (!authctx.state.user.emailVerified) {
      navigate("verify-email");
    } else if (authctx.state.isAuthenticated) {
      navigate("/dashboard");
    }
  }, [authctx, navigate]);

  return (
    <Routes>
      {/* Public */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/verify-email" element={<EmailVerificationPage />} />
      {/* <Route path="/mfa" element={<MFAPage />} /> */}
      {/* <Route path="/mfa/setup" element={<MFASetupPage />} />
      <Route path="/mfa/verify" element={<MFAVerifyPage />} /> */}

      {/* Protected */}
      <Route path="/dashboard" element={<DashboardPage />} />

      {/* <Route
        path="/plaid/add"
        element={
          <RequireAuth>
            <AddPlaidItemPage />
          </RequireAuth>
        }
      /> */}

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
