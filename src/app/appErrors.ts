// apiErrors.ts
export type AppErrorCode =
  | "auth/no-current-user"
  | "auth/invalid-credential"
  | "auth/multi-factor-auth-required"
  | "auth/too-many-requests"
  | "network/offline"
  | "unknown";

export class AppError extends Error {
  code: AppErrorCode;
  details?: unknown;

  constructor(code: AppErrorCode, message: string, details?: unknown) {
    super(message);
    this.name = "AppError";
    this.code = code;
    this.details = details;
    console.log("AppError: ", message);
  }
}

export function isAppError(e: unknown): e is AppError {
  return e instanceof AppError;
}
