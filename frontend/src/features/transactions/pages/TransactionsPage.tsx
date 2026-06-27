import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { useAuthSession } from "@/features/auth/session/AuthSessionProvider";
import { useAccountsQuery } from "@/features/connections/api/queries";
import { useHouseholdQuery } from "@/features/household/api/queries";
import { useTransactionsQuery } from "@/features/transactions/api/queries";
import { useViewerQuery } from "@/features/viewer/api/queries";
import { AppShell } from "@/shared/ui/AppShell/AppShell";
import { Button } from "@/shared/ui/Button/Button";
import { PageSection } from "@/shared/ui/PageSection/PageSection";
import { TextField } from "@/shared/ui/TextField/TextField";

import styles from "@/features/transactions/pages/TransactionsPage.module.css";

const DEFAULT_LIMIT = 50;

type FilterState = {
  accountIds: string[];
  search: string;
  startDate: string;
  endDate: string;
  orderBy: "date" | "merchant" | "account" | "category" | "amount" | "pending";
  orderDirection: "asc" | "desc";
};

function filtersFromSearchParams(searchParams: URLSearchParams): FilterState {
  const accountIds = searchParams.get("account_ids");

  return {
    accountIds: accountIds
      ? accountIds.split(",").map((value) => value.trim()).filter(Boolean)
      : [],
    search: searchParams.get("search") ?? "",
    startDate: searchParams.get("start_date") ?? "",
    endDate: searchParams.get("end_date") ?? "",
    orderBy:
      (searchParams.get("order_by") as FilterState["orderBy"] | null) ?? "date",
    orderDirection:
      (searchParams.get("order_direction") as FilterState["orderDirection"] | null) ??
      "desc",
  };
}

function buildSearchParams(filters: FilterState, cursor?: string | null) {
  const next = new URLSearchParams();

  if (filters.accountIds.length > 0) {
    next.set("account_ids", filters.accountIds.join(","));
  }
  if (filters.search.trim() !== "") {
    next.set("search", filters.search.trim());
  }
  if (filters.startDate !== "") {
    next.set("start_date", filters.startDate);
  }
  if (filters.endDate !== "") {
    next.set("end_date", filters.endDate);
  }
  if (filters.orderBy !== "date") {
    next.set("order_by", filters.orderBy);
  }
  if (filters.orderDirection !== "desc") {
    next.set("order_direction", filters.orderDirection);
  }
  if (cursor) {
    next.set("cursor", cursor);
  }

  return next;
}

function formatCurrency(amount: string, currency: string | null) {
  const numericAmount = Number(amount);
  const safeCurrency = currency || "USD";

  try {
    return new Intl.NumberFormat(undefined, {
      style: "currency",
      currency: safeCurrency,
    }).format(numericAmount);
  } catch {
    return `${numericAmount.toFixed(2)} ${safeCurrency}`;
  }
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(new Date(value));
}

export default function TransactionsPage() {
  const { logout, user } = useAuthSession();
  const viewerQuery = useViewerQuery({ enabled: true });
  const householdQuery = useHouseholdQuery({ enabled: true });
  const accountsQuery = useAccountsQuery({ enabled: true });
  const [searchParams, setSearchParams] = useSearchParams();
  const appliedFilters = filtersFromSearchParams(searchParams);
  const [filters, setFilters] = useState<FilterState>(() =>
    filtersFromSearchParams(searchParams)
  );
  const [cursorHistory, setCursorHistory] = useState<string[]>([]);

  useEffect(() => {
    setFilters(filtersFromSearchParams(searchParams));
  }, [searchParams]);

  const cursor = searchParams.get("cursor");
  const transactionQuery = useTransactionsQuery({
    accountIds: appliedFilters.accountIds,
    search: appliedFilters.search.trim() || undefined,
    startDate: appliedFilters.startDate || undefined,
    endDate: appliedFilters.endDate || undefined,
    orderBy: appliedFilters.orderBy,
    orderDirection: appliedFilters.orderDirection,
    cursor,
    limit: DEFAULT_LIMIT,
  });

  const title =
    householdQuery.data?.name ?? viewerQuery.data?.name ?? "Transactions";

  const accountOptions =
    accountsQuery.data?.items.flatMap((connection) =>
      (connection.accounts ?? []).map((account) => ({
        id: account.id,
        label: `${account.name}${connection.institution_name ? ` · ${connection.institution_name}` : ""}`,
      }))
    ) ?? [];

  const handleAccountChange = (values: string[]) => {
    setFilters((current) => ({
      ...current,
      accountIds: values,
    }));
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

  const applyFilters = () => {
    setCursorHistory([]);
    setSearchParams(buildSearchParams(filters));
  };

  const resetFilters = () => {
    const nextFilters = {
      accountIds: [],
      search: "",
      startDate: "",
      endDate: "",
      orderBy: "date" as const,
      orderDirection: "desc" as const,
    };
    setFilters(nextFilters);
    setCursorHistory([]);
    setSearchParams(buildSearchParams(nextFilters));
  };

  const goToNextPage = () => {
    if (!transactionQuery.data?.page.next_cursor) {
      return;
    }

    setCursorHistory((current) => [...current, cursor ?? ""]);
    setSearchParams(
      buildSearchParams(appliedFilters, transactionQuery.data.page.next_cursor)
    );
  };

  const goToPreviousPage = () => {
    if (cursorHistory.length === 0) {
      return;
    }

    const previousCursor = cursorHistory[cursorHistory.length - 1];
    setCursorHistory((current) => current.slice(0, -1));
    setSearchParams(
      buildSearchParams(
        appliedFilters,
        previousCursor === "" ? null : previousCursor
      )
    );
  };

  return (
    <AppShell
      title={title}
      subtitle="Inspect synced transactions with account, search, and date filters."
      email={user?.email ?? viewerQuery.data?.email}
      onLogout={logout}
    >
      <div className={styles.layout}>
        <PageSection title="Filters">
          <div className={styles.filterGrid}>
            <TextField
              label="Search"
              value={filters.search}
              placeholder="Merchant or raw description"
              onChange={(value) =>
                setFilters((current) => ({ ...current, search: value }))
              }
            />

            <div className={styles.field}>
              <label className={styles.label} htmlFor="transactions-start-date">
                Start date
              </label>
              <input
                id="transactions-start-date"
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
              <label className={styles.label} htmlFor="transactions-end-date">
                End date
              </label>
              <input
                id="transactions-end-date"
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

          <div className={styles.filterGrid}>
            <div className={styles.field}>
              <label className={styles.label} htmlFor="transactions-order-by">
                Order by
              </label>
              <select
                id="transactions-order-by"
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
                <option value="account">Account</option>
                <option value="category">Category</option>
                <option value="amount">Amount</option>
                <option value="pending">Pending</option>
              </select>
            </div>

            <div className={styles.field}>
              <label className={styles.label} htmlFor="transactions-order-direction">
                Direction
              </label>
              <select
                id="transactions-order-direction"
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
                onClick={() =>
                  handleAccountChange(accountOptions.map((account) => account.id))
                }
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
            <div className={styles.accountPicker} aria-label="Accounts">
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
              Leave everything unchecked to search across all accounts.
            </p>
          </div>

          <div className={styles.actions}>
            <Button onClick={applyFilters}>Apply filters</Button>
            <Button variant="secondary" onClick={resetFilters}>
              Reset
            </Button>
          </div>
        </PageSection>

        <PageSection title="Ledger">
          {transactionQuery.isLoading ? (
            <p className={styles.summary}>Loading transactions…</p>
          ) : null}

          {transactionQuery.isError ? (
            <p className={styles.summary}>
              {transactionQuery.error instanceof Error
                ? transactionQuery.error.message
                : "Failed to load transactions."}
            </p>
          ) : null}

          {transactionQuery.data ? (
            <>
              <p className={styles.summary}>
                Showing {transactionQuery.data.items.length} of{" "}
                {transactionQuery.data.page.total_count} matching transactions.
              </p>

              {transactionQuery.data.items.length === 0 ? (
                <p className={styles.empty}>No transactions match these filters.</p>
              ) : (
                <div className={styles.tableWrapper}>
                  <table className={styles.table}>
                    <thead>
                      <tr>
                        <th className={styles.th}>Date</th>
                        <th className={styles.th}>Merchant</th>
                        <th className={styles.th}>Account</th>
                        <th className={styles.th}>Category</th>
                        <th className={styles.th}>Amount</th>
                      </tr>
                    </thead>
                    <tbody>
                      {transactionQuery.data.items.map((transaction) => (
                        <tr key={transaction.id}>
                          <td className={styles.td}>
                            {formatDate(transaction.occurred_at)}
                          </td>
                          <td className={styles.td}>
                            <div className={styles.merchantCell}>
                              <span className={styles.merchantName}>
                                {transaction.merchant_name ?? "Unknown merchant"}
                              </span>
                              {transaction.pending ? (
                                <span className={styles.pendingTag}>Pending</span>
                              ) : null}
                              {transaction.original_description &&
                              transaction.original_description !==
                                transaction.merchant_name ? (
                                <span className={styles.description}>
                                  {transaction.original_description}
                                </span>
                              ) : null}
                            </div>
                          </td>
                          <td className={styles.td}>
                            <div className={styles.accountCell}>
                              <span className={styles.accountName}>
                                {transaction.account_name ?? "Unnamed account"}
                              </span>
                              {transaction.institution_name ? (
                                <span className={styles.institutionName}>
                                  {transaction.institution_name}
                                </span>
                              ) : null}
                            </div>
                          </td>
                          <td className={styles.td}>
                            <div className={styles.categoryCell}>
                              <span className={styles.categoryPrimary}>
                                {transaction.category_primary ?? "Uncategorized"}
                              </span>
                              {transaction.category_detailed ? (
                                <span className={styles.categoryDetailed}>
                                  {transaction.category_detailed}
                                </span>
                              ) : null}
                            </div>
                          </td>
                          <td className={styles.td}>
                            <span
                              className={
                                Number(transaction.amount) < 0
                                  ? styles.amountNegative
                                  : styles.amountPositive
                              }
                            >
                              {formatCurrency(
                                transaction.amount,
                                transaction.iso_currency_code
                              )}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              <div className={styles.pager}>
                <p className={styles.pagerText}>
                  Sorted by {appliedFilters.orderBy} {appliedFilters.orderDirection}.
                </p>
                <div className={styles.pagerActions}>
                  <Button
                    variant="secondary"
                    disabled={cursorHistory.length === 0 || transactionQuery.isFetching}
                    onClick={goToPreviousPage}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="secondary"
                    disabled={
                      !transactionQuery.data.page.has_next_page ||
                      transactionQuery.isFetching
                    }
                    onClick={goToNextPage}
                  >
                    Next
                  </Button>
                </div>
              </div>
            </>
          ) : null}
        </PageSection>
      </div>
    </AppShell>
  );
}
