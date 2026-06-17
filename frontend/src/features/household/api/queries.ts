import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import {
  createHousehold,
  getMyHousehold,
  getMyMembership,
  joinHousehold,
} from "@/features/household/api/client";

export const householdKeys = {
  all: ["household"] as const,
  membership: () => [...householdKeys.all, "membership"] as const,
  current: () => [...householdKeys.all, "current"] as const,
};

type HouseholdQueryOptions = {
  enabled?: boolean;
};

export function useMembershipQuery(options: HouseholdQueryOptions = {}) {
  return useQuery({
    queryKey: householdKeys.membership(),
    queryFn: getMyMembership,
    enabled: options.enabled,
  });
}

export function useHouseholdQuery(options: HouseholdQueryOptions = {}) {
  return useQuery({
    queryKey: householdKeys.current(),
    queryFn: getMyHousehold,
    enabled: options.enabled,
  });
}

export function useCreateHouseholdMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createHousehold,
    onSuccess: () =>
      Promise.all([
        queryClient.invalidateQueries({ queryKey: householdKeys.membership() }),
        queryClient.invalidateQueries({ queryKey: householdKeys.current() }),
      ]),
  });
}

export function useJoinHouseholdMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: joinHousehold,
    onSuccess: () =>
      Promise.all([
        queryClient.invalidateQueries({ queryKey: householdKeys.membership() }),
        queryClient.invalidateQueries({ queryKey: householdKeys.current() }),
      ]),
  });
}
