import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import {
  addItem,
  createLinkToken,
  getAccounts,
  getConnections,
  revokeConnection,
  updateAccountTracking,
} from "@/features/connections/api/client";

export const connectionsKeys = {
  all: ["connections"] as const,
  items: () => [...connectionsKeys.all, "items"] as const,
  accounts: () => [...connectionsKeys.all, "accounts"] as const,
};

type ConnectionsQueryOptions = {
  enabled?: boolean;
};

export function useConnectionsQuery(options: ConnectionsQueryOptions = {}) {
  return useQuery({
    queryKey: connectionsKeys.items(),
    queryFn: getConnections,
    enabled: options.enabled,
  });
}

export function useAccountsQuery(options: ConnectionsQueryOptions = {}) {
  return useQuery({
    queryKey: connectionsKeys.accounts(),
    queryFn: getAccounts,
    enabled: options.enabled,
  });
}

export function useCreateLinkTokenMutation() {
  return useMutation({
    mutationFn: createLinkToken,
  });
}

export function useAddItemMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: addItem,
    onSuccess: () =>
      Promise.all([
        queryClient.invalidateQueries({ queryKey: connectionsKeys.items() }),
        queryClient.invalidateQueries({ queryKey: connectionsKeys.accounts() }),
      ]),
  });
}

export function useRefreshConnections() {
  const queryClient = useQueryClient();

  return () =>
    Promise.all([
      queryClient.invalidateQueries({ queryKey: connectionsKeys.items() }),
      queryClient.invalidateQueries({ queryKey: connectionsKeys.accounts() }),
    ]);
}

export function useRevokeConnectionMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: revokeConnection,
    onSuccess: () =>
      Promise.all([
        queryClient.invalidateQueries({ queryKey: connectionsKeys.items() }),
        queryClient.invalidateQueries({ queryKey: connectionsKeys.accounts() }),
      ]),
  });
}

export function useUpdateAccountTrackingMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      accountId,
      is_query_tracking_enabled,
    }: {
      accountId: string;
      is_query_tracking_enabled: boolean;
    }) => updateAccountTracking(accountId, { is_query_tracking_enabled }),
    onSuccess: () =>
      Promise.all([
        queryClient.invalidateQueries({ queryKey: connectionsKeys.items() }),
        queryClient.invalidateQueries({ queryKey: connectionsKeys.accounts() }),
      ]),
  });
}
