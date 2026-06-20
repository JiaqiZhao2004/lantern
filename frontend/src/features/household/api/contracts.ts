import type { JsonRequest, JsonResponse } from "@/shared/api/openapi";

export const CREATE_HOUSEHOLD_PATH = "/households/create" as const;
export const GET_MY_HOUSEHOLD_PATH = "/households/me/household" as const;
export const GET_MY_MEMBERSHIP_PATH = "/households/me/membership" as const;
export const JOIN_HOUSEHOLD_PATH_TEMPLATE = "/households/{household_id}/join" as const;

export type CreateHouseholdRequest = JsonRequest<
  typeof CREATE_HOUSEHOLD_PATH,
  "post"
>;
export type Household = JsonResponse<typeof GET_MY_HOUSEHOLD_PATH, "get">;
export type Membership = JsonResponse<typeof GET_MY_MEMBERSHIP_PATH, "get">;
export type JoinHouseholdResponse = JsonResponse<
  typeof JOIN_HOUSEHOLD_PATH_TEMPLATE,
  "post"
>;
