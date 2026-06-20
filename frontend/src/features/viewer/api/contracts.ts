import type { JsonResponse } from "@/shared/api/openapi";

export const USERS_ME_PATH = "/users/me" as const;

export type Viewer = JsonResponse<typeof USERS_ME_PATH, "post">;
