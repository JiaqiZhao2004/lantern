import { AppError } from "../../../../core/appErrors";
import axiosClient from "../../../../core/axiosConfig";
import {
  CREATE_LINK_TOKEN_API_PATH,
  CreateLinkTokenResponse,
  GET_INFO_API_PATH,
  GetInfoResponse,
} from "./dto";

export class PlaidService {

  static async plaidGetInfo() {
    try {
      const res = await axiosClient.post<GetInfoResponse>(GET_INFO_API_PATH);
      return res.data;
    } catch (error) {
      throw new AppError("link/backend-down", "Plaid backend is down", error);
    }
  }

  static async plaidCreateLinkToken() {
    try {
      const res = await axiosClient.post<CreateLinkTokenResponse>(
        CREATE_LINK_TOKEN_API_PATH
      );
      if ((res as any).data.error) {
        throw new AppError(
          "link/create-link-token-failed",
          "Failed to create Plaid link token: " + (res as any).data.error
        );
      }
      return (res as any).data.link_token;
    } catch (error) {
      throw new AppError(
        "link/create-link-token-failed",
        "Failed to create Plaid link token",
        error
      );
    }
  }
}

export class BackendService {

  saveAccessToken() {
    // axiosClient
  }
  

}