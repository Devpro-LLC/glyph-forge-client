# glyph_forge/core/client/exceptions.py
"""
Exception hierarchy for ForgeClient.

All exceptions inherit from ForgeClientError for easy catching.
"""

from __future__ import annotations
from typing import Optional, Any


class ForgeClientError(Exception):
    """Base exception for all ForgeClient errors."""

    def __init__(
        self,
        message: str,
        *,
        endpoint: Optional[str] = None,
        payload_summary: Optional[str] = None,
    ):
        self.message = message
        self.endpoint = endpoint
        self.payload_summary = payload_summary
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        parts = [self.message]
        if self.endpoint:
            parts.append(f"endpoint={self.endpoint}")
        if self.payload_summary:
            parts.append(f"payload={self.payload_summary}")
        return " | ".join(parts)


class ForgeClientIOError(ForgeClientError):
    """Network or connection-related errors (timeouts, DNS failures, etc.)."""

    def __init__(
        self,
        message: str,
        *,
        endpoint: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        self.original_error = original_error
        super().__init__(message, endpoint=endpoint)

    def _format_message(self) -> str:
        base = super()._format_message()
        if self.original_error:
            return f"{base} | cause={type(self.original_error).__name__}: {self.original_error}"
        return base


class ForgeClientHTTPError(ForgeClientError):
    """HTTP errors (non-2xx status codes)."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        response_body: Optional[str] = None,
        endpoint: Optional[str] = None,
    ):
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(message, endpoint=endpoint)

    def _format_message(self) -> str:
        base = super()._format_message()
        parts = [base, f"status={self.status_code}"]
        if self.response_body:
            # Truncate long bodies
            body_preview = self.response_body[:200]
            if len(self.response_body) > 200:
                body_preview += "..."
            parts.append(f"body={body_preview}")
        return " | ".join(parts)