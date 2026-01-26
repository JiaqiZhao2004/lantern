import { paths } from "../../../../core/backendDTOTypes";

export const GET_INFO_API_PATH = "/api/v1/plaid/info";
export type GetInfoResponse =
  paths[typeof GET_INFO_API_PATH]["post"]["responses"]["200"]["content"]["application/json"];

export const CREATE_LINK_TOKEN_API_PATH = "/api/v1/plaid/create_link_token";
export type CreateLinkTokenResponse =
  paths[typeof CREATE_LINK_TOKEN_API_PATH]["post"]["responses"]["200"]["content"]["application/json"];