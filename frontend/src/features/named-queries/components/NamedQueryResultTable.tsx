import styles from "@/features/named-queries/components/NamedQueryResultTable.module.css";
import type { ColumnMeta } from "@/features/named-queries/api/contracts";

type Props = {
  columns: ColumnMeta[];
  rows: Record<string, unknown>[];
  truncated: boolean;
};

function isSingleValueResult(
  columns: ColumnMeta[],
  rows: Record<string, unknown>[]
) {
  return columns.length === 1 && rows.length === 1;
}

export function NamedQueryResultTable({
  columns,
  rows,
  truncated,
}: Props) {
  if (rows.length === 0) {
    return <p className={styles.empty}>No results.</p>;
  }

  if (isSingleValueResult(columns, rows)) {
    const label = columns[0].name;
    const value = rows[0][label];

    return (
      <div>
        <div className={styles.singleValue}>
          <p className={styles.singleValueNumber}>{formatCellValue(value)}</p>
          <p className={styles.singleValueLabel}>{label}</p>
        </div>
        {truncated && (
          <p className={styles.truncated}>
            Showing the first 50 rows — refine your query to see more.
          </p>
        )}
      </div>
    );
  }

  return (
    <div>
      <div className={styles.wrapper}>
        <table className={styles.table}>
          <thead>
            <tr>
              {columns.map((col) => (
                <th key={col.name} className={styles.th}>
                  {col.name}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr key={i}>
                {columns.map((col) => (
                  <td key={col.name} className={styles.td}>
                    {formatCellValue(row[col.name])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {truncated && (
        <p className={styles.truncated}>
          Showing the first 50 rows — refine your query to see more.
        </p>
      )}
    </div>
  );
}

function formatCellValue(value: unknown) {
  if (value == null) {
    return "";
  }

  if (typeof value === "string" && isMidnightUtcTimestamp(value)) {
    return value.slice(0, 10);
  }

  return String(value);
}

function isMidnightUtcTimestamp(value: string) {
  return /^\d{4}-\d{2}-\d{2}T00:00:00(?:\.000)?Z$/.test(value);
}
