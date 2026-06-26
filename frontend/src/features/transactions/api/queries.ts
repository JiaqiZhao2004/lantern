import { useQuery } from "@tanstack/react-query";

import { getTransactions } from "@/features/transactions/api/client";
import type { ListTransactionsParams } from "@/features/transactions/api/contracts";

export const transactionsKeys = {
  all: ["transactions"] as const,
  list: (params: ListTransactionsParams) =>
    [...transactionsKeys.all, "list", params] as const,
};

export function useTransactionsQuery(params: ListTransactionsParams) {
  return useQuery({
    queryKey: transactionsKeys.list(params),
    queryFn: () => getTransactions(params),
  });
}
