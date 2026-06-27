export const LIST_TRANSACTIONS_PATH = "/transactions" as const;

export type TransactionLedgerItem = {
  id: string;
  account_id: string;
  account_name: string | null;
  institution_name: string | null;
  occurred_at: string;
  amount: string;
  merchant_name: string | null;
  original_description: string | null;
  pending: boolean;
  category_primary: string | null;
  category_detailed: string | null;
  iso_currency_code: string | null;
};

export type TransactionLedgerResponse = {
  items: TransactionLedgerItem[];
  page: {
    next_cursor: string | null;
    has_next_page: boolean;
    total_count: number;
    limit: number;
  };
};

export type ListTransactionsParams = {
  accountIds?: string[];
  search?: string;
  startDate?: string;
  endDate?: string;
  orderBy?: "date" | "merchant" | "account" | "category" | "amount" | "pending";
  orderDirection?: "asc" | "desc";
  cursor?: string | null;
  limit?: number;
};
