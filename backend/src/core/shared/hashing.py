"""
Hashing utilities for PII data (email, phone).

Follows Meta Conversions API hashing standard:
- Normalize → lowercase, strip whitespace
- Phone: digits only (no +, spaces, dashes)
- SHA-256 hex digest

These hashes are used for:
1. `value_sha256` column on ContactEmail/ContactPhone (deduplication + CAPI)
2. `_em` / `_ph` cookies (first-party hashed PII for ad matching)
3. Meta CAPI `user_data.em` / `user_data.ph` fields

Reference: https://developers.facebook.com/docs/marketing-api/conversions-api/parameters/customer-information-parameters
"""

from __future__ import annotations

import hashlib
import re


def hash_email(email: str) -> str:
    """Hash email following Meta standard: lowercase, strip, SHA-256.

    Args:
        email: Raw email address.

    Returns:
        64-char lowercase hex SHA-256 digest.

    Raises:
        ValueError: If email is empty after normalization.
    """
    normalized = email.lower().strip()
    if not normalized:
        raise ValueError("Cannot hash empty email")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def hash_phone(phone: str) -> str:
    """Hash phone following Meta standard: digits only, SHA-256.

    Strips all non-digit characters (country code, +, spaces, dashes).
    The result is the SHA-256 of the pure digit string.

    Args:
        phone: Raw phone number in any format.

    Returns:
        64-char lowercase hex SHA-256 digest.

    Raises:
        ValueError: If phone has no digits after normalization.
    """
    digits = re.sub(r"[^\d]", "", phone)
    if not digits:
        raise ValueError("Cannot hash phone with no digits")
    return hashlib.sha256(digits.encode("utf-8")).hexdigest()
