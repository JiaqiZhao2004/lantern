import axios from "axios";
import axiosClient from "../../../../core/axiosConfig";
import {
  CREATE_HOUSEHOLD_API_PATH,
  CreateHouseholdRequest,
  GET_MY_HOUSEHOLD_API_PATH,
  GET_MY_MEMBERSHIP_API_PATH,
  HouseholdResponse,
  MembershipResponse,
} from "./dto";

export async function create_household(
  payload: CreateHouseholdRequest
): Promise<HouseholdResponse> {
  const res = await axiosClient.post<HouseholdResponse>(
    CREATE_HOUSEHOLD_API_PATH,
    payload
  );
  return res.data;
}

export async function get_my_membership(): Promise<MembershipResponse | null> {
  try {
    const res = await axiosClient.get<MembershipResponse>(GET_MY_MEMBERSHIP_API_PATH);
    return res.data;
  } catch (error) {
    if (axios.isAxiosError(error) && error.response?.status === 404) {
      return null;
    }
    throw error;
  }
}

export async function get_my_household(): Promise<HouseholdResponse> {
  const res = await axiosClient.get<HouseholdResponse>(GET_MY_HOUSEHOLD_API_PATH);
  return res.data;
}
