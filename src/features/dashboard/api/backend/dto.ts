import { paths } from "../../../../core/backendDTOTypes";

export const USERS_ME_API_PATH = "/api/v1/users/me";
export const GET_MY_HOUSEHOLD_API_PATH = "/api/v1/households/me/household";

export type UserResponse =
  paths[typeof USERS_ME_API_PATH]["post"]["responses"]["200"]["content"]["application/json"];

export type HouseholdResponse =
  paths[typeof GET_MY_HOUSEHOLD_API_PATH]["get"]["responses"]["200"]["content"]["application/json"];

export const GET_ITEMS_API_PATH = "/api/v1/plaid/items";

export type GetItemsResponse =
  paths[typeof GET_ITEMS_API_PATH]["get"]["responses"]["200"]["content"]["application/json"];

export type PlaidItem = GetItemsResponse["items"][number];

export const GET_ACCOUNTS_API_PATH = "/api/v1/plaid/accounts";

export type GetAccountsResponse =
  paths[typeof GET_ACCOUNTS_API_PATH]["get"]["responses"]["200"]["content"]["application/json"];

export type ItemWithAccounts = GetAccountsResponse["items"][number];
export type Account = ItemWithAccounts["accounts"][number];
