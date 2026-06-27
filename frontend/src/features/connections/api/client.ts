import {
  ADD_ITEM_PATH,
  CREATE_LINK_TOKEN_PATH,
  GET_ACCOUNTS_PATH,
  GET_ITEMS_PATH,
  type AddItemRequest,
  type AddItemResponse,
  type CreateLinkTokenResponse,
  type GetAccountsResponse,
  type GetItemsResponse,
  type UpdateAccountTrackingRequest,
  revokeItemPath,
  updateAccountPath,
} from "@/features/connections/api/contracts";
import httpClient from "@/shared/api/httpClient";

export async function createLinkToken(): Promise<CreateLinkTokenResponse> {
  const response = await httpClient.post<CreateLinkTokenResponse>(
    CREATE_LINK_TOKEN_PATH
  );
  return response.data;
}

export async function addItem(
  payload: AddItemRequest
): Promise<AddItemResponse> {
  const body = new URLSearchParams();
  body.set("link_public_token", payload.link_public_token);

  const response = await httpClient.post<AddItemResponse>(ADD_ITEM_PATH, body, {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
  });

  return response.data;
}

export async function getConnections(): Promise<GetItemsResponse> {
  const response = await httpClient.get<GetItemsResponse>(GET_ITEMS_PATH);
  return response.data;
}

export async function getAccounts(): Promise<GetAccountsResponse> {
  const response = await httpClient.get<GetAccountsResponse>(GET_ACCOUNTS_PATH);
  return response.data;
}

export async function revokeConnection(connectionId: string): Promise<void> {
  await httpClient.delete(revokeItemPath(connectionId));
}

export async function updateAccountTracking(
  accountId: string,
  payload: UpdateAccountTrackingRequest
): Promise<void> {
  await httpClient.patch(updateAccountPath(accountId), payload);
}
