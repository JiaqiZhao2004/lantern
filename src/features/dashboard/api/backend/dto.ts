import { paths } from "../../../../core/backendDTOTypes";

export const USERS_ME_API_PATH = "/api/v1/users/me";

export type UserResponse =
  paths[typeof USERS_ME_API_PATH]["post"]["responses"]["200"]["content"]["application/json"];

export const GET_ITEMS_API_PATH = "/api/v1/plaid/items";

export type GetItemsResponse =
  paths[typeof GET_ITEMS_API_PATH]["get"]["responses"]["200"]["content"]["application/json"];

export type PlaidItem = GetItemsResponse["items"][number];
