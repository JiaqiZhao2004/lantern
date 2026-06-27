import { useEffect, useState } from "react";
import { NamedQueryResultTable } from "@/features/named-queries/components/NamedQueryResultTable";
import type { NamedQueryDataResponse } from "@/features/named-queries/api/contracts";
import styles from "@/features/named-queries/components/NamedQueryTransactionPreview.module.css";
import { Button } from "@/shared/ui/Button/Button";
import { TextField } from "@/shared/ui/TextField/TextField";

type FilterState = {
  accountIds: string[];
  search: string;
  startDate: string;
  endDate: string;
  orderBy: "date" | "merchant" | "amount" | "category" | "pending";
  orderDirection: "asc" | "desc";
};

type AccountOption = {
  id: string;
  label: string;
};

type Props = {
  preview: NonNullable<NamedQueryDataResponse["transaction_preview"]>;
  accountOptions: AccountOption[];
  appliedFilters: FilterState;
  isUpdating: boolean;
  onApplyFilters: (filters: FilterState) => void;
  onResetFilters: () => void;
};

export function NamedQueryTransactionPreview({
  preview,
  accountOptions,
  appliedFilters,
  isUpdating,
  onApplyFilters,
  onResetFilters,
}: Props) {
  const [filters, setFilters] = useState<FilterState>(appliedFilters);

  useEffect(() => {
    setFilters(appliedFilters);
  }, [appliedFilters]);

  const handleAccountChange = (accountIds: string[]) => {
    setFilters((current) => ({ ...current, accountIds }));
  };

  const toggleAccount = (accountId: string) => {
    setFilters((current) => {
      const alreadySelected = current.accountIds.includes(accountId);

      return {
        ...current,
        accountIds: alreadySelected
          ? current.accountIds.filter((value) => value !== accountId)
          : [...current.accountIds, accountId],
      };
    });
  };

  return (
    <section className={styles.section}>
      <div className={styles.header}>
        <h4 className={styles.title}>Matching transactions</h4>
        <p className={styles.hint}>
          Preview a simplified sample of matching transactions so you can correct the
          query if it is pulling the wrong activity.
        </p>
      </div>

      <div className={styles.filterGrid}>
        <TextField
          label="Search"
          value={filters.search}
          placeholder="Merchant or raw description"
          onChange={(search) =>
            setFilters((current) => ({
              ...current,
              search,
            }))
          }
        />

        <div className={styles.field}>
          <label className={styles.label} htmlFor="named-query-preview-start-date">
            Start date
          </label>
          <input
            id="named-query-preview-start-date"
            className={styles.dateInput}
            type="date"
            value={filters.startDate}
            onChange={(event) =>
              setFilters((current) => ({
                ...current,
                startDate: event.target.value,
              }))
            }
          />
        </div>

        <div className={styles.field}>
          <label className={styles.label} htmlFor="named-query-preview-end-date">
            End date
          </label>
          <input
            id="named-query-preview-end-date"
            className={styles.dateInput}
            type="date"
            value={filters.endDate}
            onChange={(event) =>
              setFilters((current) => ({
                ...current,
                endDate: event.target.value,
              }))
            }
          />
        </div>
      </div>

      <div className={styles.accountField}>
        <div className={styles.accountHeader}>
          <label className={styles.label}>Accounts</label>
          <span className={styles.selectionCount}>
            {filters.accountIds.length === 0
              ? "All accounts"
              : `${filters.accountIds.length} selected`}
          </span>
        </div>

        <div className={styles.accountActions}>
          <button
            type="button"
            className={styles.accountAction}
            onClick={() => handleAccountChange(accountOptions.map((account) => account.id))}
          >
            Select all
          </button>
          <button
            type="button"
            className={styles.accountAction}
            onClick={() => handleAccountChange([])}
          >
            Clear
          </button>
        </div>

        <div className={styles.accountPicker} aria-label="Filter preview accounts">
          {accountOptions.map((account) => (
            <label key={account.id} className={styles.accountOption}>
              <input
                type="checkbox"
                className={styles.accountCheckbox}
                checked={filters.accountIds.includes(account.id)}
                onChange={() => toggleAccount(account.id)}
              />
              <span className={styles.accountOptionLabel}>{account.label}</span>
            </label>
          ))}
        </div>

        <p className={styles.hint}>
          Leave everything unchecked to preview matching transactions across all
          accounts.
        </p>
      </div>

      <div className={styles.filterGrid}>
        <div className={styles.field}>
          <label className={styles.label} htmlFor="named-query-preview-order-by">
            Order by
          </label>
          <select
            id="named-query-preview-order-by"
            className={styles.select}
            value={filters.orderBy}
            onChange={(event) =>
              setFilters((current) => ({
                ...current,
                orderBy: event.target.value as FilterState["orderBy"],
              }))
            }
          >
            <option value="date">Date</option>
            <option value="merchant">Merchant</option>
            <option value="amount">Amount</option>
            <option value="category">Category</option>
            <option value="pending">Pending</option>
          </select>
        </div>

        <div className={styles.field}>
          <label className={styles.label} htmlFor="named-query-preview-order-direction">
            Direction
          </label>
          <select
            id="named-query-preview-order-direction"
            className={styles.select}
            value={filters.orderDirection}
            onChange={(event) =>
              setFilters((current) => ({
                ...current,
                orderDirection: event.target.value as FilterState["orderDirection"],
              }))
            }
          >
            <option value="desc">Descending</option>
            <option value="asc">Ascending</option>
          </select>
        </div>
      </div>

      <div className={styles.actions}>
        <Button onClick={() => onApplyFilters(filters)} disabled={isUpdating}>
          {isUpdating ? "Updating…" : "Apply filters"}
        </Button>
        <Button variant="secondary" onClick={onResetFilters} disabled={isUpdating}>
          Reset
        </Button>
      </div>

      <NamedQueryResultTable
        columns={preview.columns}
        rows={preview.rows as Record<string, unknown>[]}
        truncated={preview.truncated}
      />
    </section>
  );
}
