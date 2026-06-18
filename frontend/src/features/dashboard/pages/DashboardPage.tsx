import { useNavigate } from "react-router-dom";
import styles from "@/features/dashboard/pages/DashboardPage.module.css";
import { useAuthSession } from "@/features/auth/session/AuthSessionProvider";
import { useHouseholdQuery } from "@/features/household/api/queries";
import { useViewerQuery } from "@/features/viewer/api/queries";
import { NamedQueryCard } from "@/features/named-queries/components/NamedQueryCard";
import { useNamedQueriesQuery } from "@/features/named-queries/api/queries";
import { AppShell } from "@/shared/ui/AppShell/AppShell";
import { Button } from "@/shared/ui/Button/Button";
import { PageSection } from "@/shared/ui/PageSection/PageSection";

export default function DashboardPage() {
  const { logout, user } = useAuthSession();
  const viewerQuery = useViewerQuery({ enabled: true });
  const householdQuery = useHouseholdQuery({ enabled: true });
  const namedQueriesQuery = useNamedQueriesQuery();
  const navigate = useNavigate();

  const title =
    householdQuery.data?.name ?? viewerQuery.data?.name ?? "Dashboard";

  return (
    <AppShell
      title={title}
      email={user?.email ?? viewerQuery.data?.email}
      onLogout={logout}
    >
      <div className={styles.grid}>
        <PageSection
          title="Named Queries"
          action={
            <Button onClick={() => navigate("/queries/new")}>
              + New Query
            </Button>
          }
        >
          {namedQueriesQuery.isLoading && (
            <p style={{ color: "var(--text-muted)" }}>Loading…</p>
          )}
          {namedQueriesQuery.isError && (
            <p style={{ color: "var(--danger-700)" }}>
              {namedQueriesQuery.error instanceof Error
                ? namedQueriesQuery.error.message
                : "Failed to load Named Queries."}
            </p>
          )}
          {namedQueriesQuery.data && namedQueriesQuery.data.length === 0 && (
            <p style={{ color: "var(--text-muted)" }}>
              No Named Queries yet.{" "}
              <button
                style={{
                  background: "none",
                  border: "none",
                  color: "var(--brand-700)",
                  cursor: "pointer",
                  font: "inherit",
                  fontWeight: 600,
                  padding: 0,
                }}
                onClick={() => navigate("/queries/new")}
              >
                Create your first one.
              </button>
            </p>
          )}
          {namedQueriesQuery.data && namedQueriesQuery.data.length > 0 && (
            <div className={styles.queryGrid}>
              {namedQueriesQuery.data.map((query) => (
                <NamedQueryCard key={query.id} query={query} />
              ))}
            </div>
          )}
        </PageSection>
      </div>
    </AppShell>
  );
}
