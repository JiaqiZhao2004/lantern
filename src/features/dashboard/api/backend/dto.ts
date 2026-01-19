import { paths } from "../../../../app/backendDTOTypes";

export const USERS_ME_API_PATH = "/api/v1/users/me";


export type UserResponse =
  paths[typeof USERS_ME_API_PATH]["post"]["responses"]["200"]["content"]["application/json"];
