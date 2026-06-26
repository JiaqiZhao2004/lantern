import { useState } from "react";
import { useNavigate } from "react-router-dom";
import classNames from "classnames";
import styles from "@/features/named-queries/components/NamedQueryCard.module.css";
import { NamedQueryChart } from "@/features/named-queries/components/NamedQueryChart";
import { NamedQueryResultTable } from "@/features/named-queries/components/NamedQueryResultTable";
import {
  useDeleteNamedQueryMutation,
  useNamedQueryDataQuery,
} from "@/features/named-queries/api/queries";
import { isKnownChartType } from "@/features/named-queries/api/contracts";
import type { NamedQueryResponse } from "@/features/named-queries/api/contracts";
import { Button } from "@/shared/ui/Button/Button";
import { Card } from "@/shared/ui/Card/Card";
import { InlineMessage } from "@/shared/ui/InlineMessage/InlineMessage";

type Props = {
  query: NamedQueryResponse;
};

export function NamedQueryCard({ query }: Props) {
  const navigate = useNavigate();
  const chartType = isKnownChartType(query.chart_type) ? query.chart_type : null;
  const [view, setView] = useState<"chart" | "table">(chartType ? "chart" : "table");

  const dataQuery = useNamedQueryDataQuery(query.id);
  const deleteMutation = useDeleteNamedQueryMutation();

  const handleDelete = () => {
    if (window.confirm(`Delete "${query.name}"?`)) {
      deleteMutation.mutate(query.id);
    }
  };

  return (
    <Card padding="md">
      <div className={styles.card}>
        <div className={styles.header}>
          <div className={styles.titleRow}>
            <h3 className={styles.name}>{query.name}</h3>
            {query.chart_type && (
              <span className={styles.chartTypeBadge}>{query.chart_type}</span>
            )}
          </div>
          <div className={styles.actions}>
            {chartType && dataQuery.data && (
              <div className={styles.toggle}>
                <button
                  className={classNames(styles.toggleBtn, view === "chart" && styles.active)}
                  onClick={() => setView("chart")}
                >
                  Chart
                </button>
                <button
                  className={classNames(styles.toggleBtn, view === "table" && styles.active)}
                  onClick={() => setView("table")}
                >
                  Table
                </button>
              </div>
            )}
            <Button
              variant="secondary"
              onClick={() => navigate(`/queries/${query.id}/edit`)}
            >
              Edit
            </Button>
            <Button
              variant="ghost"
              onClick={handleDelete}
              disabled={deleteMutation.isPending}
            >
              Delete
            </Button>
          </div>
        </div>

        <div className={styles.body}>
          {dataQuery.isLoading && <p className={styles.loading}>Loading…</p>}

          {dataQuery.isError && (
            <div className={styles.error}>
              <InlineMessage tone="error">
                <p className={styles.errorText}>
                  {dataQuery.error instanceof Error
                    ? dataQuery.error.message
                    : "This query couldn't run."}
                </p>
              </InlineMessage>
              <div>
                <Button variant="secondary" onClick={() => navigate(`/queries/${query.id}/edit`)}>
                  Edit query
                </Button>
              </div>
            </div>
          )}

          {dataQuery.data && (
            <>
              {view === "chart" && chartType ? (
                <NamedQueryChart
                  chartType={chartType}
                  columns={dataQuery.data.columns}
                  rows={dataQuery.data.rows as Record<string, unknown>[]}
                />
              ) : (
                <NamedQueryResultTable
                  columns={dataQuery.data.columns}
                  rows={dataQuery.data.rows as Record<string, unknown>[]}
                  truncated={dataQuery.data.truncated}
                />
              )}
            </>
          )}
        </div>
      </div>
    </Card>
  );
}
