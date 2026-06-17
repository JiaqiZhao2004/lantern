import type { JsonRequest, JsonResponse } from "@/shared/api/openapi";

export const CREATE_HOUSEHOLD_PATH = "/api/v1/households/create" as const;
export const GET_MY_HOUSEHOLD_PATH = "/api/v1/households/me/household" as const;
export const GET_MY_MEMBERSHIP_PATH = "/api/v1/households/me/membership" as const;
export const JOIN_HOUSEHOLD_PATH_TEMPLATE =
  "/api/v1/households/{household_id}/join" as const;

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
