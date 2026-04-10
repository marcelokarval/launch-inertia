"""
Security event detection and alerting.
"""
import logging
from typing import Optional, Dict, List, Callable
from datetime import datetime, timedelta

from django.core.cache import cache
from django.conf import settings

from .events import SecurityEvent, EventSeverity, EventType

logger = logging.getLogger(__name__)


class SecurityEventDetector:
    """
    Detects and responds to security events.

    Features:
    - Event logging
    - Threshold-based alerting
    - Pattern detection (brute force, etc.)
    - Automatic responses (account locking, etc.)
    """

    # Alert thresholds
    FAILED_LOGIN_THRESHOLD = 5
    RATE_LIMIT_THRESHOLD = 10
    IDOR_THRESHOLD = 3

    def __init__(self):
        self.alert_handlers: List[Callable[[SecurityEvent], None]] = []

    def record(self, event: SecurityEvent) -> None:
        """
        Record a security event.

        Logs the event and triggers alerts if thresholds are exceeded.
        """
        # Always log the event
        log_level = self._get_log_level(event.severity)
        logger.log(log_level, str(event), extra=event.to_dict())

        # Check patterns and thresholds
        self._check_thresholds(event)

        # Trigger alert handlers for high/critical events
        if event.severity in (EventSeverity.HIGH, EventSeverity.CRITICAL):
            self._trigger_alerts(event)

    def add_alert_handler(self, handler: Callable[[SecurityEvent], None]) -> None:
        """Add a custom alert handler."""
        self.alert_handlers.append(handler)

    def _get_log_level(self, severity: EventSeverity) -> int:
        """Map severity to log level."""
        mapping = {
            EventSeverity.LOW: logging.INFO,
            EventSeverity.MEDIUM: logging.WARNING,
            EventSeverity.HIGH: logging.ERROR,
            EventSeverity.CRITICAL: logging.CRITICAL,
        }
        return mapping.get(severity, logging.INFO)

    def _trigger_alerts(self, event: SecurityEvent) -> None:
        """Trigger all registered alert handlers."""
        for handler in self.alert_handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Alert handler failed: {e}")

    def _check_thresholds(self, event: SecurityEvent) -> None:
        """Check if event exceeds configured thresholds."""
        if event.event_type == EventType.LOGIN_FAILED:
            self._check_failed_logins(event)
        elif event.event_type == EventType.RATE_LIMIT_EXCEEDED:
            self._check_rate_limit_abuse(event)
        elif event.event_type == EventType.IDOR_ATTEMPT:
            self._check_idor_attempts(event)

    def _check_failed_logins(self, event: SecurityEvent) -> None:
        """Check for brute force login attempts."""
        if not event.ip_address:
            return

        key = f"security:failed_login:{event.ip_address}"
        count = cache.get(key, 0) + 1
        cache.set(key, count, 3600)  # 1 hour window

        if count >= self.FAILED_LOGIN_THRESHOLD:
            # Create high severity event
            alert_event = SecurityEvent(
                event_type=EventType.SUSPICIOUS_ACTIVITY,
                severity=EventSeverity.HIGH,
                ip_address=event.ip_address,
                details={
                    "reason": "Multiple failed login attempts",
                    "count": count,
                    "threshold": self.FAILED_LOGIN_THRESHOLD,
                }
            )
            self._trigger_alerts(alert_event)

    def _check_rate_limit_abuse(self, event: SecurityEvent) -> None:
        """Check for rate limit abuse patterns."""
        if not event.ip_address:
            return

        key = f"security:rate_limit:{event.ip_address}"
        count = cache.get(key, 0) + 1
        cache.set(key, count, 3600)

        if count >= self.RATE_LIMIT_THRESHOLD:
            alert_event = SecurityEvent(
                event_type=EventType.SUSPICIOUS_ACTIVITY,
                severity=EventSeverity.HIGH,
                ip_address=event.ip_address,
                details={
                    "reason": "Repeated rate limit violations",
                    "count": count,
                }
            )
            self._trigger_alerts(alert_event)

    def _check_idor_attempts(self, event: SecurityEvent) -> None:
        """Check for IDOR attack patterns."""
        if not event.user_id:
            return

        key = f"security:idor:{event.user_id}"
        count = cache.get(key, 0) + 1
        cache.set(key, count, 3600)

        if count >= self.IDOR_THRESHOLD:
            alert_event = SecurityEvent(
                event_type=EventType.SUSPICIOUS_ACTIVITY,
                severity=EventSeverity.CRITICAL,
                user_id=event.user_id,
                ip_address=event.ip_address,
                details={
                    "reason": "Multiple IDOR attempts detected",
                    "count": count,
                }
            )
            self._trigger_alerts(alert_event)

    # Convenience methods for common events
    def record_failed_login(
        self,
        ip_address: str,
        email: Optional[str] = None
    ) -> None:
        """Record a failed login attempt."""
        self.record(SecurityEvent(
            event_type=EventType.LOGIN_FAILED,
            severity=EventSeverity.MEDIUM,
            ip_address=ip_address,
            details={"email": email} if email else {},
        ))

    def record_successful_login(
        self,
        user_id: str,
        ip_address: str
    ) -> None:
        """Record a successful login."""
        self.record(SecurityEvent(
            event_type=EventType.LOGIN_SUCCESS,
            severity=EventSeverity.LOW,
            user_id=user_id,
            ip_address=ip_address,
        ))

    def record_account_locked(
        self,
        user_id: str,
        reason: str,
        ip_address: Optional[str] = None
    ) -> None:
        """Record an account being locked."""
        self.record(SecurityEvent(
            event_type=EventType.ACCOUNT_LOCKED,
            severity=EventSeverity.HIGH,
            user_id=user_id,
            ip_address=ip_address,
            details={"reason": reason},
        ))

    def record_unauthorized_access(
        self,
        user_id: Optional[str],
        ip_address: str,
        path: str,
        resource: Optional[str] = None
    ) -> None:
        """Record an unauthorized access attempt."""
        self.record(SecurityEvent(
            event_type=EventType.UNAUTHORIZED_ACCESS,
            severity=EventSeverity.HIGH,
            user_id=user_id,
            ip_address=ip_address,
            path=path,
            details={"resource": resource} if resource else {},
        ))

    def record_idor_attempt(
        self,
        user_id: str,
        ip_address: str,
        path: str,
        target_id: str
    ) -> None:
        """Record an IDOR attempt."""
        self.record(SecurityEvent(
            event_type=EventType.IDOR_ATTEMPT,
            severity=EventSeverity.HIGH,
            user_id=user_id,
            ip_address=ip_address,
            path=path,
            details={"target_id": target_id},
        ))


# Global detector instance
security_detector = SecurityEventDetector()
