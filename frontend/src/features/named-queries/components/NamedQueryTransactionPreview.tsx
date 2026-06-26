import { NamedQueryResultTable } from "@/features/named-queries/components/NamedQueryResultTable";
import type { NamedQueryDataResponse } from "@/features/named-queries/api/contracts";
import styles from "@/features/named-queries/components/NamedQueryTransactionPreview.module.css";

type Props = {
  preview: NonNullable<NamedQueryDataResponse["transaction_preview"]>;
};

export function NamedQueryTransactionPreview({ preview }: Props) {
  return (
    <section className={styles.section}>
      <div className={styles.header}>
        <h4 className={styles.title}>Matching transactions</h4>
        <p className={styles.hint}>
          Preview the raw transaction rows behind this result so you can correct the
          query if it is pulling the wrong activity.
        </p>
      </div>

      <NamedQueryResultTable
        columns={preview.columns}
        rows={preview.rows as Record<string, unknown>[]}
        truncated={preview.truncated}
      />
    </section>
  );
}
