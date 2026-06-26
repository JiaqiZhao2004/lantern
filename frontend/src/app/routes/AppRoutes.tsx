import { Navigate, Route, Routes } from "react-router-dom";
import LoginPage from "@/features/auth/pages/LoginPage";
import RegisterPage from "@/features/auth/pages/RegisterPage";
import EmailVerificationPage from "@/features/auth/pages/EmailVerificationPage";
import DashboardPage from "@/features/dashboard/pages/DashboardPage";
import HouseholdSetupPage from "@/features/household/pages/HouseholdSetupPage";
import SettingsPage from "@/features/settings/pages/SettingsPage";
import NamedQueryEditorPage from "@/features/named-queries/pages/NamedQueryEditorPage";
import PublicOverviewPage from "@/features/public-overview/pages/PublicOverviewPage";
import {
  EmailVerificationLayout,
  HouseholdRequiredLayout,
  HouseholdSetupLayout,
  PublicOnlyLayout,
  VerifiedSessionLayout,
} from "@/app/routes/RouteLayouts";

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<PublicOverviewPage />} />

      <Route element={<PublicOnlyLayout />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
      </Route>

      <Route element={<EmailVerificationLayout />}>
        <Route path="/verify-email" element={<EmailVerificationPage />} />
      </Route>

      <Route element={<VerifiedSessionLayout />}>
        <Route element={<HouseholdSetupLayout />}>
          <Route path="/household/setup" element={<HouseholdSetupPage />} />
        </Route>

        <Route element={<HouseholdRequiredLayout />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/queries/new" element={<NamedQueryEditorPage />} />
          <Route path="/queries/:id/edit" element={<NamedQueryEditorPage />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate replace to="/" />} />
    </Routes>
  );
}
