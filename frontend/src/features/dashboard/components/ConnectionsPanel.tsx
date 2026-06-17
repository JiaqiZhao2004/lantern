import { PlaidItem } from "@/features/connections/api/contracts";
import styles from "@/features/dashboard/components/Panels.module.css";
import { Card } from "@/shared/ui/Card/Card";
import { InlineMessage } from "@/shared/ui/InlineMessage/InlineMessage";

type ConnectionsPanelProps = {
  items: PlaidItem[];
  isLoading: boolean;
  errorMessage: string | null;
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
}: ConnectionsPanelProps) {
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
                </tr>
              ))}
            </tbody>
          </table>
        ) : null}
      </div>
    </Card>
  );
}
