// src/app/routes.tsx
import React, { useContext, useEffect, useState } from "react";
import {
  Navigate,
  Route,
  Routes,
  useLocation,
  useNavigate,
} from "react-router-dom";

import LoginPage from "../features/auth/pages/LoginPage";
import DashboardPage from "../features/dashboard/pages/DashboardPage";

import RegisterPage from "../features/auth/pages/RegisterPage";
// import MFAPage from "../features/auth/pages/MFAPage";
import EmailVerificationPage from "../features/auth/pages/EmailVerificationPage";
import { AuthContext } from "../features/auth/state/AuthContext";
import HouseholdSetupPage from "../features/household/pages/HouseholdSetupPage";
import { get_my_membership } from "../features/household/api/backend/client";
// import MFASetupPage from "../features/auth/pages/MFASetupPage";
// import MFAVerifyPage from "../features/auth/pages/MFAVerifyPage";

export function AppRoutes() {
  const authctx = useContext(AuthContext);
  const navigate = useNavigate();
  const location = useLocation();
  const [isCheckingMembership, setIsCheckingMembership] = useState(false);

  // All auth routing is based on AuthContext
  useEffect(() => {
    let isCancelled = false;

    const syncRoute = async () => {
      if (authctx.isLoading) {
        return;
      }

      if (!authctx?.user) {
        if (location.pathname === "/register" || location.pathname === "/login") {
          return;
        }
        navigate("/login", { replace: true });
        return;
      }

      if (!authctx.user.emailVerified) {
        if (location.pathname !== "/verify-email") {
          navigate("/verify-email", { replace: true });
        }
        return;
      }

      setIsCheckingMembership(true);

      try {
        const membership = await get_my_membership();

        if (isCancelled) {
          return;
        }

        if (membership) {
          if (
            location.pathname === "/household/setup" ||
            location.pathname === "/login" ||
            location.pathname === "/register" ||
            location.pathname === "/verify-email"
          ) {
            navigate("/dashboard", { replace: true });
          }
          return;
        }

        if (location.pathname !== "/household/setup") {
          navigate("/household/setup", { replace: true });
        }
      } finally {
        if (!isCancelled) {
          setIsCheckingMembership(false);
        }
      }
    };

    syncRoute();

    return () => {
      isCancelled = true;
    };
  }, [
    authctx.isLoading,
    authctx.user,
    authctx.user?.emailVerified,
    location.pathname,
    navigate,
  ]);

  if (authctx.isLoading || isCheckingMembership) {
    return (
      <div
        style={{
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          backgroundColor: "#f5f5f5",
          color: "#555",
        }}
      >
        Loading...
      </div>
    );
  }

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
      <Route path="/household/setup" element={<HouseholdSetupPage />} />
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
