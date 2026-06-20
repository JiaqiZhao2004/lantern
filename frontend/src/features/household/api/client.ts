import {
  CREATE_HOUSEHOLD_PATH,
  GET_MY_HOUSEHOLD_PATH,
  GET_MY_MEMBERSHIP_PATH,
  type CreateHouseholdRequest,
  type Household,
  type JoinHouseholdResponse,
  type Membership,
} from "@/features/household/api/contracts";
import { isAppError } from "@/shared/api/appError";
import httpClient from "@/shared/api/httpClient";

export async function createHousehold(
  payload: CreateHouseholdRequest
): Promise<Household> {
  const response = await httpClient.post<Household>(CREATE_HOUSEHOLD_PATH, payload);
  return response.data;
}

export async function getMyMembership(): Promise<Membership | null> {
  try {
    const response = await httpClient.get<Membership>(GET_MY_MEMBERSHIP_PATH);
    return response.data;
  } catch (error) {
    if (isAppError(error) && error.code === "api/not-found") {
      return null;
    }

    throw error;
  }
}

export async function getMyHousehold(): Promise<Household> {
  const response = await httpClient.get<Household>(GET_MY_HOUSEHOLD_PATH);
  return response.data;
}

export async function joinHousehold(
  householdId: string
): Promise<JoinHouseholdResponse> {
  const response = await httpClient.post<JoinHouseholdResponse>(
    `/households/${householdId}/join`
  );
  return response.data;
}
