// src/app/routes.tsx
import React from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import LoginPage from "../features/auth/pages/LoginPage";
import DashboardPage from "../features/dashboard/pages/DashboardPage";
// import AddPlaidItemPage from "../features/plaid/pages/AddPlaidItemPage";

import { RequireAuth } from "../features/auth/RequireAuth";
import RegisterPage from "../features/auth/pages/RegisterPage";
import MFAPage from "../features/auth/pages/MFAPage";
import EmailVerificationPage from "../features/auth/pages/EmailVerificationPage";
import MFASetupPage from "../features/auth/pages/MFASetupPage";
import MFAVerifyPage from "../features/auth/pages/MFAVerifyPage";

export function AppRoutes() {
  return (
    <Routes>
      {/* Public */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/verify-email" element={<EmailVerificationPage />} />
      <Route path="/mfa" element={<MFAPage />} />
      <Route path="/mfa/setup" element={<MFASetupPage />} />
      <Route path="/mfa/verify" element={<MFAVerifyPage />} />

      {/* Protected */}
      <Route
        path="/"
        element={
          <RequireAuth>
            <DashboardPage />
          </RequireAuth>
        }
      />

      {/* <Route
        path="/plaid/add"
        element={
          <RequireAuth>
            <AddPlaidItemPage />
          </RequireAuth>
        }
      /> */}

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
