import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createNamedQuery,
  deleteNamedQuery,
  generateNamedQueryCandidate,
  getNamedQueryData,
  listNamedQueries,
  patchNamedQuery,
  previewNamedQuery,
} from "@/features/named-queries/api/client";
import type {
  CreateNamedQueryRequest,
  GenerateNamedQueryRequest,
  PatchNamedQueryRequest,
  PreviewNamedQueryRequest,
} from "@/features/named-queries/api/contracts";

export const namedQueriesKeys = {
  all: ["named-queries"] as const,
  list: () => [...namedQueriesKeys.all, "list"] as const,
  data: (id: string) => [...namedQueriesKeys.all, "data", id] as const,
};

export function useNamedQueriesQuery() {
  return useQuery({
    queryKey: namedQueriesKeys.list(),
    queryFn: listNamedQueries,
  });
}

export function useNamedQueryDataQuery(id: string) {
  return useQuery({
    queryKey: namedQueriesKeys.data(id),
    queryFn: () => getNamedQueryData(id),
    retry: false,
  });
}

export function useCreateNamedQueryMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateNamedQueryRequest) => createNamedQuery(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: namedQueriesKeys.list() }),
  });
}

export function usePatchNamedQueryMutation(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: PatchNamedQueryRequest) => patchNamedQuery(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: namedQueriesKeys.list() });
      queryClient.invalidateQueries({ queryKey: namedQueriesKeys.data(id) });
    },
  });
}

export function useDeleteNamedQueryMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteNamedQuery(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: namedQueriesKeys.list() }),
  });
}

export function usePreviewNamedQueryMutation() {
  return useMutation({
    mutationFn: (payload: PreviewNamedQueryRequest) => previewNamedQuery(payload),
    retry: false,
  });
}

export function useGenerateNamedQueryMutation() {
  return useMutation({
    mutationFn: (payload: GenerateNamedQueryRequest) =>
      generateNamedQueryCandidate(payload),
    retry: false,
  });
}
