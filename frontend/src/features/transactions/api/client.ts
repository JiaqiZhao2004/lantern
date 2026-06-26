import httpClient from "@/shared/api/httpClient";
import {
  LIST_TRANSACTIONS_PATH,
  type ListTransactionsParams,
  type TransactionLedgerResponse,
} from "@/features/transactions/api/contracts";

export async function getTransactions(
  params: ListTransactionsParams
): Promise<TransactionLedgerResponse> {
  const response = await httpClient.get<TransactionLedgerResponse>(
    LIST_TRANSACTIONS_PATH,
    {
      params: {
        account_ids:
          params.accountIds && params.accountIds.length > 0
            ? params.accountIds.join(",")
            : undefined,
        search: params.search || undefined,
        start_date: params.startDate || undefined,
        end_date: params.endDate || undefined,
        cursor: params.cursor || undefined,
        limit: params.limit,
      },
    }
  );

  return response.data;
}
