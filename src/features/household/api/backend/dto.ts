import { paths } from "../../../../core/backendDTOTypes";

export const CREATE_HOUSEHOLD_API_PATH = "/api/v1/households/create";
export const GET_MY_MEMBERSHIP_API_PATH = "/api/v1/households/me/membership";
export const GET_MY_HOUSEHOLD_API_PATH = "/api/v1/households/me/household";

export type CreateHouseholdRequest =
  paths[typeof CREATE_HOUSEHOLD_API_PATH]["post"]["requestBody"]["content"]["application/json"];

export type HouseholdResponse =
  paths[typeof GET_MY_HOUSEHOLD_API_PATH]["get"]["responses"]["200"]["content"]["application/json"];

export type MembershipResponse =
  paths[typeof GET_MY_MEMBERSHIP_API_PATH]["get"]["responses"]["200"]["content"]["application/json"];
