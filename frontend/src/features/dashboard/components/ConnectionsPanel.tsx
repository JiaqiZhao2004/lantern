import { useMemo, useState } from "react";
import { PlaidItem } from "@/features/connections/api/contracts";
import styles from "@/features/dashboard/components/Panels.module.css";
import { Button } from "@/shared/ui/Button/Button";
import { Card } from "@/shared/ui/Card/Card";
import { InlineMessage } from "@/shared/ui/InlineMessage/InlineMessage";

type ConnectionsPanelProps = {
  items: PlaidItem[];
  isLoading: boolean;
  errorMessage: string | null;
  onRevoke: (connectionId: string) => void;
  revokingConnectionId: string | null;
};

function formatDate(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export default function ConnectionsPanel({
  errorMessage,
  isLoading,
  items,
  onRevoke,
  revokingConnectionId,
}: ConnectionsPanelProps) {
  const [pendingConnectionId, setPendingConnectionId] = useState<string | null>(null);
  const pendingConnection = useMemo(
    () => items.find((item) => item.id === pendingConnectionId) ?? null,
    [items, pendingConnectionId]
  );

  if (errorMessage) {
    return <InlineMessage tone="error">{errorMessage}</InlineMessage>;
  }

  return (
    <Card padding="md">
      <div className={styles.cardStack}>
        {isLoading ? <p className={styles.empty}>Loading connections...</p> : null}
        {!isLoading && items.length === 0 ? (
          <p className={styles.empty}>No connected institutions yet.</p>
        ) : null}

        {!isLoading && items.length > 0 ? (
          <table className={styles.table}>
            <thead>
              <tr>
                <th className={styles.th}>Institution</th>
                <th className={styles.th}>Status</th>
                <th className={styles.th}>Updated</th>
                <th className={styles.th}>Action</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id}>
                  <td className={styles.td}>
                    {item.institution_name ?? "Unnamed institution"}
                  </td>
                  <td className={styles.td}>
                    <span className={styles.chip}>{item.status}</span>
                  </td>
                  <td className={styles.td}>{formatDate(item.updated_at)}</td>
                  <td className={styles.td}>
                    {item.can_revoke && item.status === "active" ? (
                      <Button
                        variant="ghost"
                        onClick={() => setPendingConnectionId(item.id)}
                        disabled={revokingConnectionId !== null}
                      >
                        Revoke access
                      </Button>
                    ) : (
                      <span className={styles.empty}>Unavailable</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : null}
      </div>

      {pendingConnection ? (
        <div className={styles.overlay} role="dialog" aria-modal="true">
          <Card style={{ width: "100%", maxWidth: "32rem" }}>
            <div className={styles.cardStack}>
              <div>
                <h3 className={styles.modalTitle}>Revoke access?</h3>
                <p className={styles.modalBody}>
                  Revoking access for{" "}
                  <strong>
                    {pendingConnection.institution_name ?? "this institution"}
                  </strong>{" "}
                  will delete all accounts and transactions from that connection.
                  You will need to relink it later. Your named queries will not be
                  deleted.
                </p>
              </div>

              <div className={styles.modalActions}>
                <Button
                  variant="secondary"
                  onClick={() => setPendingConnectionId(null)}
                  disabled={revokingConnectionId !== null}
                >
                  Cancel
                </Button>
                <Button
                  onClick={() => {
                    onRevoke(pendingConnection.id);
                    setPendingConnectionId(null);
                  }}
                  disabled={revokingConnectionId !== null}
                >
                  {revokingConnectionId === pendingConnection.id
                    ? "Revoking..."
                    : "Revoke access"}
                </Button>
              </div>
            </div>
          </Card>
        </div>
      ) : null}
    </Card>
  );
}
