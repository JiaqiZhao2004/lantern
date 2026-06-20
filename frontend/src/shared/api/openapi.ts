import type { paths } from "@/core/backendDTOTypes";

type Defined<T> = Exclude<T, undefined | null | never>;
type ApiVersionPrefix = "/api/v1";
type PrefixedPath<TPath extends string> =
  TPath extends `${ApiVersionPrefix}${string}` ? TPath : `${ApiVersionPrefix}${TPath}`;
type ResolvedPath<TPath extends string> = PrefixedPath<TPath> & keyof paths;
type OperationMethod<TPath extends string> = keyof paths[ResolvedPath<TPath>];
type Operation<TPath extends string, TMethod extends OperationMethod<TPath>> = Defined<
  paths[ResolvedPath<TPath>][TMethod]
>;

export type JsonResponse<
  TPath extends string,
  TMethod extends OperationMethod<TPath> = OperationMethod<TPath>
> = Operation<TPath, TMethod> extends {
  responses: { 200: { content: { "application/json": infer TResponse } } };
}
  ? TResponse
  : never;

export type JsonCreatedResponse<
  TPath extends string,
  TMethod extends OperationMethod<TPath> = OperationMethod<TPath>
> = Operation<TPath, TMethod> extends {
  responses: { 201: { content: { "application/json": infer TResponse } } };
}
  ? TResponse
  : never;

export type JsonRequest<
  TPath extends string,
  TMethod extends OperationMethod<TPath> = OperationMethod<TPath>
> = Operation<TPath, TMethod> extends {
  requestBody: { content: { "application/json": infer TRequest } };
}
  ? TRequest
  : never;

export type FormRequest<
  TPath extends string,
  TMethod extends OperationMethod<TPath> = OperationMethod<TPath>
> = Operation<TPath, TMethod> extends {
  requestBody: {
    content: { "application/x-www-form-urlencoded": infer TRequest };
  };
}
  ? TRequest
  : never;
