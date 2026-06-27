import type { FormRequest, JsonResponse } from "@/shared/api/openapi";

export const CREATE_LINK_TOKEN_PATH = "/plaid/create_link_token" as const;
export const ADD_ITEM_PATH = "/plaid/item" as const;
export const GET_ITEMS_PATH = "/plaid/items" as const;
export const GET_ACCOUNTS_PATH = "/plaid/accounts" as const;
export const updateAccountPath = (accountId: string) =>
  `/plaid/accounts/${accountId}` as const;
export const revokeItemPath = (connectionId: string) =>
  `/plaid/item/${connectionId}` as const;

export type CreateLinkTokenResponse = JsonResponse<
  typeof CREATE_LINK_TOKEN_PATH,
  "post"
>;
export type AddItemRequest = FormRequest<typeof ADD_ITEM_PATH, "post">;
export type AddItemResponse = unknown;
export type GetItemsResponse = JsonResponse<typeof GET_ITEMS_PATH, "get">;
type ApiGetAccountsResponse = JsonResponse<typeof GET_ACCOUNTS_PATH, "get">;
export type PlaidItem = GetItemsResponse["items"][number];
type ApiItemWithAccounts = ApiGetAccountsResponse["items"][number];
type ApiAccount = NonNullable<ApiItemWithAccounts["accounts"]>[number];

export type Account = ApiAccount & {
  is_query_tracking_enabled: boolean;
};

export type ItemWithAccounts = Omit<ApiItemWithAccounts, "accounts"> & {
  accounts: Account[];
};

export type GetAccountsResponse = Omit<ApiGetAccountsResponse, "items"> & {
  items: ItemWithAccounts[];
};

export type UpdateAccountTrackingRequest = {
  is_query_tracking_enabled: boolean;
};
