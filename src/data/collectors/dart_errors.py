"""DART API error classes."""


class DartAPIError(Exception):
    """Base exception for DART API errors."""

    def __init__(self, message: str, status: str = "") -> None:
        """Initialize DartAPIError.

        Args:
            message: Error message
            status: DART API status code
        """
        super().__init__(message)
        self.status = status


class DartNoDataError(DartAPIError):
    """Exception raised when DART API returns status 013 (no data)."""

    pass


class DartRateLimitError(DartAPIError):
    """Exception raised when DART API returns status 020 (rate limit exceeded)."""

    pass
