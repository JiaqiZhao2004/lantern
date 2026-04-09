import httpClient from "@/shared/api/httpClient";
import { USERS_ME_PATH, type Viewer } from "@/features/viewer/api/contracts";

export async function getOrCreateViewer(): Promise<Viewer> {
  const response = await httpClient.post<Viewer>(USERS_ME_PATH);
  return response.data;
}
