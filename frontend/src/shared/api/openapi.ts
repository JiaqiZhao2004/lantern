import type { paths } from "@/core/backendDTOTypes";

type Defined<T> = Exclude<T, undefined | null | never>;
type ApiVersionPrefix = "/api/v1";
type PrefixedPath<TPath extends string> =
  TPath extends `${ApiVersionPrefix}${string}` ? TPath : `${ApiVersionPrefix}${TPath}`;
type Operation<
  TPath extends string,
  TMethod extends keyof paths[PrefixedPath<TPath> & keyof paths]
> = Defined<paths[TPath][TMethod]>;

export type JsonResponse<
  TPath extends string,
  TResolvedPath extends PrefixedPath<TPath> & keyof paths = PrefixedPath<TPath> &
    keyof paths,
  TMethod extends keyof paths[TResolvedPath] = keyof paths[TResolvedPath]
> = Operation<TPath, TMethod> extends {
  responses: { 200: { content: { "application/json": infer TResponse } } };
}
  ? TResponse
  : never;

export type JsonCreatedResponse<
  TPath extends string,
  TResolvedPath extends PrefixedPath<TPath> & keyof paths = PrefixedPath<TPath> &
    keyof paths,
  TMethod extends keyof paths[TResolvedPath] = keyof paths[TResolvedPath]
> = Operation<TPath, TMethod> extends {
  responses: { 201: { content: { "application/json": infer TResponse } } };
}
  ? TResponse
  : never;

export type JsonRequest<
  TPath extends string,
  TResolvedPath extends PrefixedPath<TPath> & keyof paths = PrefixedPath<TPath> &
    keyof paths,
  TMethod extends keyof paths[TResolvedPath] = keyof paths[TResolvedPath]
> = Operation<TPath, TMethod> extends {
  requestBody: { content: { "application/json": infer TRequest } };
}
  ? TRequest
  : never;

export type FormRequest<
  TPath extends string,
  TResolvedPath extends PrefixedPath<TPath> & keyof paths = PrefixedPath<TPath> &
    keyof paths,
  TMethod extends keyof paths[TResolvedPath] = keyof paths[TResolvedPath]
> = Operation<TPath, TMethod> extends {
  requestBody: {
    content: { "application/x-www-form-urlencoded": infer TRequest };
  };
}
  ? TRequest
  : never;
