import {
  CREATE_LINK_TOKEN_PATH,
  GET_ACCOUNTS_PATH,
  GET_ITEMS_PATH,
  type CreateLinkTokenResponse,
  type GetAccountsResponse,
  type GetItemsResponse,
} from "@/features/connections/api/contracts";
import httpClient from "@/shared/api/httpClient";

export async function createLinkToken(): Promise<CreateLinkTokenResponse> {
  const response = await httpClient.post<CreateLinkTokenResponse>(
    CREATE_LINK_TOKEN_PATH
  );
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
