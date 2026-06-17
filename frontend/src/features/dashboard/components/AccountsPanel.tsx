import { ItemWithAccounts } from "@/features/connections/api/contracts";
import styles from "@/features/dashboard/components/Panels.module.css";
import { Card } from "@/shared/ui/Card/Card";
import { InlineMessage } from "@/shared/ui/InlineMessage/InlineMessage";

type AccountsPanelProps = {
  items: ItemWithAccounts[];
  isLoading: boolean;
  errorMessage: string | null;
};

export default function AccountsPanel({
  errorMessage,
  isLoading,
  items,
}: AccountsPanelProps) {
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
            <Card key={item.item_id} padding="md">
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
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </Card>
          );
        })}
    </div>
  );
}
