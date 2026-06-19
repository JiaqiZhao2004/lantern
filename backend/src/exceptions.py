class AppError(Exception):
    status_code = 400
    detail = "Application error"

    def __init__(self, detail: str | None = None):
        super().__init__(detail or self.detail)
        self.detail = detail or self.detail


class NotFoundError(AppError):
    status_code = 404
    detail = "Resource not found"


class ConflictError(AppError):
    status_code = 409
    detail = "Resource conflict"


class ValidationError(AppError):
    status_code = 422
    detail = "Validation failed"


class RateLimitError(AppError):
    status_code = 429
    detail = "Rate limit exceeded"


class InternalError(AppError):
    status_code = 500
    detail = "Internal error"
