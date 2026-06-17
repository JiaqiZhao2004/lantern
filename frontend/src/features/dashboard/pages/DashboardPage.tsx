import styles from "@/features/dashboard/pages/DashboardPage.module.css";
import { useAuthSession } from "@/features/auth/session/AuthSessionProvider";
import { useAccountsQuery, useConnectionsQuery } from "@/features/connections/api/queries";
import { PlaidLinkCard } from "@/features/connections/components/PlaidLinkCard";
import AccountsPanel from "@/features/dashboard/components/AccountsPanel";
import ConnectionsPanel from "@/features/dashboard/components/ConnectionsPanel";
import { useHouseholdQuery } from "@/features/household/api/queries";
import { useViewerQuery } from "@/features/viewer/api/queries";
import { AppShell } from "@/shared/ui/AppShell/AppShell";
import { PageSection } from "@/shared/ui/PageSection/PageSection";

export default function DashboardPage() {
  const { logout, user } = useAuthSession();
  const viewerQuery = useViewerQuery({ enabled: true });
  const householdQuery = useHouseholdQuery({ enabled: true });
  const connectionsQuery = useConnectionsQuery({ enabled: true });
  const accountsQuery = useAccountsQuery({ enabled: true });

  const title =
    householdQuery.data?.name ?? viewerQuery.data?.name ?? "Dashboard";

  return (
    <AppShell
      title={title}
      subtitle="Review linked institutions, explore account structure, and keep the onboarding surface clean."
      email={user?.email ?? viewerQuery.data?.email}
      onLogout={logout}
    >
      <div className={styles.grid}>
        <div className={styles.topGrid}>
          <PlaidLinkCard />
        </div>

        <PageSection
          title="Linked institutions"
          description="Every institution currently visible from the backend contract."
        >
          <ConnectionsPanel
            items={connectionsQuery.data?.items ?? []}
            isLoading={connectionsQuery.isLoading}
            errorMessage={
              connectionsQuery.error instanceof Error
                ? connectionsQuery.error.message
                : null
            }
          />
        </PageSection>

        <PageSection
          title="Accounts"
          description="Accounts are grouped by institution and ordered by the backend response."
        >
          <AccountsPanel
            items={accountsQuery.data?.items ?? []}
            isLoading={accountsQuery.isLoading}
            errorMessage={
              accountsQuery.error instanceof Error
                ? accountsQuery.error.message
                : null
            }
          />
        </PageSection>
      </div>
    </AppShell>
  );
}
