import type { JsonResponse } from "@/shared/api/openapi";

export const CREATE_LINK_TOKEN_PATH = "/api/v1/plaid/create_link_token" as const;
export const GET_ITEMS_PATH = "/api/v1/plaid/items" as const;
export const GET_ACCOUNTS_PATH = "/api/v1/plaid/accounts" as const;

export type CreateLinkTokenResponse = JsonResponse<
  typeof CREATE_LINK_TOKEN_PATH,
  "post"
>;
export type GetItemsResponse = JsonResponse<typeof GET_ITEMS_PATH, "get">;
export type GetAccountsResponse = JsonResponse<typeof GET_ACCOUNTS_PATH, "get">;
export type PlaidItem = GetItemsResponse["items"][number];
export type ItemWithAccounts = GetAccountsResponse["items"][number];
export type Account = NonNullable<ItemWithAccounts["accounts"]>[number];
