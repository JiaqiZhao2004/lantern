import axiosClient from "../../../../core/axiosConfig";
import {
  GetAccountsResponse,
  GET_ACCOUNTS_API_PATH,
  GetItemsResponse,
  GET_ITEMS_API_PATH,
  GET_MY_HOUSEHOLD_API_PATH,
  HouseholdResponse,
  UserResponse,
  USERS_ME_API_PATH,
} from "./dto";

export async function get_or_create_me() {
  const res = await axiosClient.post<UserResponse>(USERS_ME_API_PATH);
  return res.data;
}

export async function get_items(): Promise<GetItemsResponse> {
  const res = await axiosClient.get<GetItemsResponse>(GET_ITEMS_API_PATH);
  return res.data;
}

export async function get_accounts(): Promise<GetAccountsResponse> {
  const res = await axiosClient.get<GetAccountsResponse>(GET_ACCOUNTS_API_PATH);
  return res.data;
}

export async function get_my_household(): Promise<HouseholdResponse> {
  const res = await axiosClient.get<HouseholdResponse>(GET_MY_HOUSEHOLD_API_PATH);
  return res.data;
}
