import httpClient from "@/shared/api/httpClient";
import type {
  CreateNamedQueryRequest,
  CreateNamedQueryResponse,
  GenerateNamedQueryRequest,
  GenerateNamedQueryResponse,
  NamedQueryDataResponse,
  NamedQueryResponse,
  PatchNamedQueryRequest,
  PatchNamedQueryResponse,
  PreviewNamedQueryRequest,
  PreviewNamedQueryResponse,
} from "@/features/named-queries/api/contracts";

export async function listNamedQueries(): Promise<NamedQueryResponse[]> {
  const response = await httpClient.get<NamedQueryResponse[]>("/api/v1/named-queries");
  return response.data;
}

export async function createNamedQuery(
  payload: CreateNamedQueryRequest
): Promise<CreateNamedQueryResponse> {
  const response = await httpClient.post<CreateNamedQueryResponse>(
    "/api/v1/named-queries",
    payload
  );
  return response.data;
}

export async function patchNamedQuery(
  id: string,
  payload: PatchNamedQueryRequest
): Promise<PatchNamedQueryResponse> {
  const response = await httpClient.patch<PatchNamedQueryResponse>(
    `/api/v1/named-queries/${id}`,
    payload
  );
  return response.data;
}

export async function deleteNamedQuery(id: string): Promise<void> {
  await httpClient.delete(`/api/v1/named-queries/${id}`);
}

export async function getNamedQueryData(id: string): Promise<NamedQueryDataResponse> {
  const response = await httpClient.get<NamedQueryDataResponse>(
    `/api/v1/named-queries/${id}/data`
  );
  return response.data;
}

export async function previewNamedQuery(
  payload: PreviewNamedQueryRequest
): Promise<PreviewNamedQueryResponse> {
  const response = await httpClient.post<PreviewNamedQueryResponse>(
    "/api/v1/named-queries/preview",
    payload
  );
  return response.data;
}

export async function generateNamedQueryCandidate(
  payload: GenerateNamedQueryRequest
): Promise<GenerateNamedQueryResponse> {
  const response = await httpClient.post<GenerateNamedQueryResponse>(
    "/api/v1/named-queries/generate",
    payload
  );
  return response.data;
}
