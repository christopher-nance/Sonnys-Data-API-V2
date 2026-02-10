"""Exception hierarchy for the Sonny's Data Client SDK."""


class SonnysError(Exception):
    pass


class APIError(SonnysError):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class APIConnectionError(APIError):
    def __init__(self, message: str = "Connection error.") -> None:
        super().__init__(message)


class APITimeoutError(APIConnectionError):
    def __init__(self, message: str = "Request timed out.") -> None:
        super().__init__(message)


class APIStatusError(APIError):
    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        body: dict | None = None,
        error_type: str | None = None,
    ) -> None:
        self.status_code = status_code
        self.body = body
        self.error_type = error_type
        super().__init__(message)


class AuthError(APIStatusError):
    pass


class RateLimitError(APIStatusError):
    pass


class ValidationError(APIStatusError):
    pass


class NotFoundError(APIStatusError):
    pass


class ServerError(APIStatusError):
    pass
