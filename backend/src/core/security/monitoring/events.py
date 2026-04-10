"""
Security event definitions.
"""
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any


class EventSeverity(Enum):
    """Security event severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EventType(Enum):
    """Types of security events."""
    # Authentication
    LOGIN_FAILED = "login_failed"
    LOGIN_SUCCESS = "login_success"
    LOGOUT = "logout"
    PASSWORD_RESET_REQUEST = "password_reset_request"
    PASSWORD_CHANGED = "password_changed"

    # Account
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_UNLOCKED = "account_unlocked"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"

    # Access
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    IDOR_ATTEMPT = "idor_attempt"

    # Data
    SENSITIVE_DATA_ACCESS = "sensitive_data_access"
    BULK_DATA_EXPORT = "bulk_data_export"

    # Admin
    ADMIN_ACTION = "admin_action"
    PERMISSION_CHANGED = "permission_changed"


@dataclass
class SecurityEvent:
    """
    Represents a security event for logging and alerting.

    Usage:
        event = SecurityEvent(
            event_type=EventType.LOGIN_FAILED,
            severity=EventSeverity.MEDIUM,
            user_id="usr_123",
            ip_address="1.2.3.4",
            details={"attempts": 3}
        )
        security_detector.record(event)
    """
    event_type: EventType
    severity: EventSeverity
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    path: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for logging/storage."""
        return {
            "event_type": self.event_type.value,
            "severity": self.severity.value,
            "user_id": self.user_id,
            "ip_address": self.ip_address,
            "path": self.path,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
        }

    def __str__(self) -> str:
        return (
            f"[{self.severity.value.upper()}] {self.event_type.value} "
            f"- User: {self.user_id or 'anonymous'} "
            f"- IP: {self.ip_address or 'unknown'}"
        )
