import { useMemo, useState } from "react";
import { ItemWithAccounts } from "@/features/connections/api/contracts";
import styles from "@/features/dashboard/components/Panels.module.css";
import { Button } from "@/shared/ui/Button/Button";
import { Card } from "@/shared/ui/Card/Card";
import { InlineMessage } from "@/shared/ui/InlineMessage/InlineMessage";

type AccountsPanelProps = {
  items: ItemWithAccounts[];
  isLoading: boolean;
  errorMessage: string | null;
  onToggleTracking: (accountId: string, nextValue: boolean) => void;
  togglingAccountId: string | null;
};

export default function AccountsPanel({
  errorMessage,
  isLoading,
  items,
  onToggleTracking,
  togglingAccountId,
}: AccountsPanelProps) {
  const [pendingAccountId, setPendingAccountId] = useState<string | null>(null);
  const pendingAccount = useMemo(
    () =>
      items
        .flatMap((item) =>
          (item.accounts ?? []).map((account) => ({
            account,
            institutionName: item.institution_name,
          }))
        )
        .find(({ account }) => account.id === pendingAccountId) ?? null,
    [items, pendingAccountId]
  );

  if (errorMessage) {
    return <InlineMessage tone="error">{errorMessage}</InlineMessage>;
  }

  return (
    <div className={styles.cardStack}>
      {isLoading ? <p className={styles.empty}>Loading accounts...</p> : null}
      {!isLoading && items.length === 0 ? (
        <Card padding="md">
          <p className={styles.empty}>No accounts found for this household yet.</p>
        </Card>
      ) : null}

      {!isLoading &&
        items.map((item) => {
          const accounts = item.accounts ?? [];

          return (
            <Card key={item.connection_id} padding="md">
              <div className={styles.institutionBlock}>
                <div>
                  <h3 className={styles.institutionTitle}>
                    {item.institution_name ?? "Unnamed institution"}
                  </h3>
                  <div className={styles.accountMeta}>
                    <span className={styles.chip}>{item.status}</span>
                    <span className={styles.chip}>{accounts.length} accounts</span>
                  </div>
                </div>

                {accounts.length === 0 ? (
                  <p className={styles.empty}>No active accounts were returned.</p>
                ) : (
                  <table className={styles.table}>
                    <thead>
                      <tr>
                        <th className={styles.th}>Name</th>
                        <th className={styles.th}>Type</th>
                        <th className={styles.th}>Subtype</th>
                        <th className={styles.th}>Mask</th>
                        <th className={styles.th}>Named Queries</th>
                      </tr>
                    </thead>
                    <tbody>
                      {accounts.map((account) => (
                        <tr key={account.id}>
                          <td className={styles.td}>{account.name}</td>
                          <td className={styles.td}>
                            {account.account_type ?? "Unspecified"}
                          </td>
                          <td className={styles.td}>
                            {account.account_subtype ?? "Unspecified"}
                          </td>
                          <td className={styles.td}>{account.mask ?? "--"}</td>
                          <td className={styles.td}>
                            <button
                              type="button"
                              role="switch"
                              aria-checked={account.is_query_tracking_enabled}
                              aria-label={`${
                                account.is_query_tracking_enabled ? "Disable" : "Enable"
                              } Named Query tracking for ${account.name}`}
                              className={styles.trackingToggle}
                              onClick={() => setPendingAccountId(account.id)}
                              disabled={togglingAccountId !== null}
                            >
                              <span
                                className={
                                  account.is_query_tracking_enabled
                                    ? styles.trackingToggleOn
                                    : styles.trackingToggleOff
                                }
                              >
                                {account.is_query_tracking_enabled ? "On" : "Off"}
                              </span>
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </Card>
          );
        })}

      {pendingAccount ? (
        <div className={styles.overlay} role="dialog" aria-modal="true">
          <Card style={{ width: "100%", maxWidth: "32rem" }}>
            <div className={styles.cardStack}>
              <div>
                <h3 className={styles.modalTitle}>
                  {pendingAccount.account.is_query_tracking_enabled
                    ? "Disable account tracking?"
                    : "Enable account tracking?"}
                </h3>
                <p className={styles.modalBody}>
                  {pendingAccount.account.is_query_tracking_enabled
                    ? "If you disable this account, your named queries will no longer track transactions from it. The named queries themselves will not be deleted."
                    : "If you enable this account, your named queries will start tracking transactions from it again. The named queries themselves will not be deleted."}
                </p>
                <p className={styles.modalBody}>
                  <strong>{pendingAccount.account.name}</strong>
                  {pendingAccount.institutionName
                    ? ` · ${pendingAccount.institutionName}`
                    : ""}
                </p>
              </div>

              <div className={styles.modalActions}>
                <Button
                  variant="secondary"
                  onClick={() => setPendingAccountId(null)}
                  disabled={togglingAccountId !== null}
                >
                  Cancel
                </Button>
                <Button
                  onClick={() => {
                    onToggleTracking(
                      pendingAccount.account.id,
                      !pendingAccount.account.is_query_tracking_enabled
                    );
                    setPendingAccountId(null);
                  }}
                  disabled={togglingAccountId !== null}
                >
                  {togglingAccountId === pendingAccount.account.id
                    ? "Saving..."
                    : pendingAccount.account.is_query_tracking_enabled
                      ? "Disable tracking"
                      : "Enable tracking"}
                </Button>
              </div>
            </div>
          </Card>
        </div>
      ) : null}
    </div>
  );
}
