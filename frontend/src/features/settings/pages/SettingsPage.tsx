import { useAuthSession } from "@/features/auth/session/AuthSessionProvider";
import {
  useAccountsQuery,
  useConnectionsQuery,
  useRevokeConnectionMutation,
} from "@/features/connections/api/queries";
import { PlaidLinkCard } from "@/features/connections/components/PlaidLinkCard";
import AccountsPanel from "@/features/dashboard/components/AccountsPanel";
import ConnectionsPanel from "@/features/dashboard/components/ConnectionsPanel";
import { useHouseholdQuery } from "@/features/household/api/queries";
import { useViewerQuery } from "@/features/viewer/api/queries";
import { AppShell } from "@/shared/ui/AppShell/AppShell";
import { PageSection } from "@/shared/ui/PageSection/PageSection";

export default function SettingsPage() {
  const { logout, user } = useAuthSession();
  const viewerQuery = useViewerQuery({ enabled: true });
  const householdQuery = useHouseholdQuery({ enabled: true });
  const connectionsQuery = useConnectionsQuery({ enabled: true });
  const accountsQuery = useAccountsQuery({ enabled: true });
  const revokeConnectionMutation = useRevokeConnectionMutation();

  return (
    <AppShell
      title="Settings"
      email={user?.email ?? viewerQuery.data?.email}
      onLogout={logout}
    >
      <PageSection title="Link an institution">
        <PlaidLinkCard />
      </PageSection>

      <PageSection title="Linked institutions">
        <ConnectionsPanel
          items={connectionsQuery.data?.items ?? []}
          isLoading={connectionsQuery.isLoading}
          errorMessage={
            connectionsQuery.error instanceof Error
              ? connectionsQuery.error.message
              : revokeConnectionMutation.error instanceof Error
                ? revokeConnectionMutation.error.message
                : null
          }
          onRevoke={(connectionId) => revokeConnectionMutation.mutate(connectionId)}
          revokingConnectionId={
            revokeConnectionMutation.isPending
              ? revokeConnectionMutation.variables ?? null
              : null
          }
        />
      </PageSection>

      <PageSection title="Accounts">
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
    </AppShell>
  );
}
