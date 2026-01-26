import { AppError } from "../../../../core/appErrors";
import axiosClient from "../../../../core/axiosConfig";
import {
  ADD_ITEM_API_PATH,
  AddItemResponse,
  CREATE_LINK_TOKEN_API_PATH,
  CreateLinkTokenResponse,
  GET_INFO_API_PATH,
  GetInfoResponse,
} from "./dto";

export class PlaidService {
  static async getInfo() {
    try {
      const res = await axiosClient.post<GetInfoResponse>(GET_INFO_API_PATH);
      return res.data;
    } catch (error) {
      throw new AppError("link/backend-down", "Plaid backend is down", error);
    }
  }

  static async createLinkToken() {
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

  static async addItem(public_token: string) {
    const res = await axiosClient.post<AddItemResponse>(
      ADD_ITEM_API_PATH,
      {
        public_token,
      },
      {
        headers: {
          "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        },
      }
    );
    console.log(res);
    return res.data;
  }
}
