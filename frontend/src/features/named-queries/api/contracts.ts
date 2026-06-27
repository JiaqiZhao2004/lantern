import type { JsonCreatedResponse, JsonRequest, JsonResponse } from "@/shared/api/openapi";

export const LIST_NAMED_QUERIES_PATH = "/named-queries" as const;
export const CREATE_NAMED_QUERY_PATH = "/named-queries" as const;
export const PREVIEW_NAMED_QUERY_PATH = "/named-queries/preview" as const;
export const GENERATE_NAMED_QUERY_PATH = "/named-queries/generate" as const;
export const NAMED_QUERY_DATA_PATH = "/named-queries/{named_query_id}/data" as const;
export const NAMED_QUERY_PATH = "/named-queries/{named_query_id}" as const;

export type NamedQueryResponse = JsonResponse<typeof LIST_NAMED_QUERIES_PATH, "get">[number];
export type NamedQueryDataResponse = JsonResponse<typeof NAMED_QUERY_DATA_PATH, "get">;
export type ColumnMeta = NamedQueryDataResponse["columns"][number];
export type QueryResultPreview = NonNullable<NamedQueryDataResponse["transaction_preview"]>;

export type CreateNamedQueryRequest = JsonRequest<typeof CREATE_NAMED_QUERY_PATH, "post">;
export type CreateNamedQueryResponse = JsonCreatedResponse<typeof CREATE_NAMED_QUERY_PATH, "post">;

export type PatchNamedQueryRequest = JsonRequest<typeof NAMED_QUERY_PATH, "patch">;
export type PatchNamedQueryResponse = JsonResponse<typeof NAMED_QUERY_PATH, "patch">;

export type PreviewNamedQueryRequest = JsonRequest<typeof PREVIEW_NAMED_QUERY_PATH, "post">;
export type PreviewNamedQueryResponse = JsonResponse<typeof PREVIEW_NAMED_QUERY_PATH, "post">;
export type TransactionPreviewFilters =
  PreviewNamedQueryRequest["transaction_preview_filters"];

export type GenerateNamedQueryRequest = JsonRequest<typeof GENERATE_NAMED_QUERY_PATH, "post">;
export type GenerateNamedQueryResponse = JsonResponse<typeof GENERATE_NAMED_QUERY_PATH, "post">;
export type NamedQueryGenerationMessage = GenerateNamedQueryRequest["messages"][number];

export type ChartType = "bar" | "line";
export const KNOWN_CHART_TYPES: ChartType[] = ["bar", "line"];

export function isKnownChartType(value: string | null | undefined): value is ChartType {
  return KNOWN_CHART_TYPES.includes(value as ChartType);
}
