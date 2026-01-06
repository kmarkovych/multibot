"""Billing-related exceptions."""

from __future__ import annotations


class InsufficientTokensError(Exception):
    """Raised when user doesn't have enough tokens for an action."""

    def __init__(
        self,
        required: int,
        available: int,
        action: str | None = None,
    ) -> None:
        self.required = required
        self.available = available
        self.action = action
        message = f"Insufficient tokens: need {required}, have {available}"
        if action:
            message = f"{message} for action '{action}'"
        super().__init__(message)
