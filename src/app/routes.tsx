// src/app/routes.tsx
import React from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import LoginPage from "../features/auth/pages/LoginPage";
import DashboardPage from "../features/dashboard/pages/DashboardPage";
// import AddPlaidItemPage from "../features/plaid/pages/AddPlaidItemPage";

import { RequireAuth } from "../features/auth/RequireAuth";

export function AppRoutes() {
  return (
    <Routes>
      {/* Public */}
      <Route path="/login" element={<LoginPage />} />

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
