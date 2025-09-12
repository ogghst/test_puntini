"""Error classifier interface for failure analysis.

This module defines the ErrorClassifier protocol that handles the classification
of failures and determination of appropriate remediation strategies.
"""

from typing import Any, Protocol
from ..orchestration.state import State


class ErrorClassifier(Protocol):
    """Protocol for classifying failures and determining remediation strategies.
    
    The error classifier analyzes failures to determine their type and
    appropriate remediation approach.
    """
    
    def classify_error(self, error: dict[str, Any]) -> str:
        """Classify an error into a specific category.

        Args:
            error: Error information including message, type, and context.

        Returns:
            Error classification: "identical", "random", or "systematic".

        Notes:
            Error classification helps determine the appropriate remediation
            strategy and retry behavior.
        """
        ...
    
    def get_remediation_strategy(self, error_type: str) -> str:
        """Get the remediation strategy for a given error type.

        Args:
            error_type: Classified error type.

        Returns:
            Remediation strategy: "retry", "diagnose", or "escalate".

        Notes:
            Different error types require different approaches:
            - identical: retry with same parameters
            - random: retry with backoff
            - systematic: diagnose and fix root cause
        """
        ...
    
    def should_retry_with_backoff(self, error_type: str) -> bool:
        """Determine if retry should use exponential backoff.

        Args:
            error_type: Classified error type.

        Returns:
            True if backoff should be used, False otherwise.

        Notes:
            Random errors benefit from backoff to avoid thundering herd
            problems, while systematic errors should not use backoff.
        """
        ...

