import type { paths } from "@/core/backendDTOTypes";

type Defined<T> = Exclude<T, undefined | null | never>;
type Operation<
  TPath extends keyof paths,
  TMethod extends keyof paths[TPath]
> = Defined<paths[TPath][TMethod]>;

export type JsonResponse<
  TPath extends keyof paths,
  TMethod extends keyof paths[TPath]
> = Operation<TPath, TMethod> extends {
  responses: { 200: { content: { "application/json": infer TResponse } } };
}
  ? TResponse
  : never;

export type JsonRequest<
  TPath extends keyof paths,
  TMethod extends keyof paths[TPath]
> = Operation<TPath, TMethod> extends {
  requestBody: { content: { "application/json": infer TRequest } };
}
  ? TRequest
  : never;

export type FormRequest<
  TPath extends keyof paths,
  TMethod extends keyof paths[TPath]
> = Operation<TPath, TMethod> extends {
  requestBody: {
    content: { "application/x-www-form-urlencoded": infer TRequest };
  };
}
  ? TRequest
  : never;
