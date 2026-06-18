import axios from "axios";

export type AppErrorCode =
  | "auth/no-current-user"
  | "auth/invalid-credential"
  | "auth/multi-factor-auth-required"
  | "auth/too-many-requests"
  | "api/not-found"
  | "api/request-failed"
  | "api/unauthorized"
  | "link/backend-down"
  | "link/create-link-token-failed"
  | "network/offline"
  | "unknown";

export class AppError extends Error {
  code: AppErrorCode;
  details?: unknown;
  status?: number;

  constructor(
    code: AppErrorCode,
    message: string,
    details?: unknown,
    status?: number
  ) {
    super(message);
    this.name = "AppError";
    this.code = code;
    this.details = details;
    this.status = status;
  }
}

export function isAppError(error: unknown): error is AppError {
  return error instanceof AppError;
}

export function normalizeApiError(error: unknown): AppError {
  if (isAppError(error)) {
    return error;
  }

  if (axios.isAxiosError(error)) {
    const status = error.response?.status;

    if (status === 401) {
      return new AppError(
        "api/unauthorized",
        "Your session has expired. Please sign in again.",
        error,
        status
      );
    }

    if (status === 404) {
      return new AppError(
        "api/not-found",
        "The requested resource was not found.",
        error,
        status
      );
    }

    if (status === 422) {
      const detail = error.response?.data?.detail;
      const message =
        typeof detail === "string"
          ? detail
          : Array.isArray(detail)
            ? detail.map((d: { msg: string }) => d.msg).join("; ")
            : "The request was invalid.";
      return new AppError("api/request-failed", message, error, status);
    }

    if (!error.response) {
      return new AppError(
        "network/offline",
        "Unable to reach the server. Check your connection and try again.",
        error
      );
    }

    return new AppError(
      "api/request-failed",
      "The request could not be completed.",
      error,
      status
    );
  }

  return new AppError("unknown", "An unexpected error occurred.", error);
}
