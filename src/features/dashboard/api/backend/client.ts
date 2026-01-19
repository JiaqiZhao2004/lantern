import axiosClient from "../../../../core/axiosConfig";
import { UserResponse, USERS_ME_API_PATH } from "./dto";

export async function get_or_create_me() {
  const res = await axiosClient.post<UserResponse>(USERS_ME_API_PATH);
  return res.data;
}
