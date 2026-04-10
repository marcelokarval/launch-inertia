"""
FingerprintJS Pro payload processing service.

Parses the FingerprintJS Pro webhook/API payload into structured data
for our fingerprint models.

Ported from legacy fingerprint/services/payload_service.py.
"""

import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class PayloadService:
    """
    Processes FingerprintJS Pro payloads and extracts structured data.
    """

    # ── Main Payload Processing ──────────────────────────────────────

    @classmethod
    def process_fingerprintjs_payload(cls, payload: dict) -> tuple[dict, dict]:
        """
        Parse a FingerprintJS Pro payload into fingerprint_data and context_data.

        FingerprintJS Pro payload structure:
        {
            "requestId": "...",
            "visitorId": "...",
            "visitorFound": true,
            "confidence": {"score": 0.99},
            "visits": [{
                "timestamp": "2024-01-01T00:00:00Z",
                "browserDetails": {...},
                "ip": "...",
                "ipLocation": {...},
                "incognito": false,
                ...
            }]
        }

        Returns:
            Tuple of (fingerprint_data: dict, context_data: dict)
        """
        visitor_id = payload.get("visitorId", "")
        visitor_found = payload.get("visitorFound", False)
        confidence = payload.get("confidence", {}).get("score", 0.0)

        # Get first visit data
        visits = payload.get("visits", [])
        visit = visits[0] if visits else {}

        browser_details = visit.get("browserDetails", {})
        ip_location = visit.get("ipLocation", {})

        # Extract structured data
        device_type = cls.classify_device_type(browser_details)

        fingerprint_data = {
            "hash": visitor_id,
            "confidence_score": confidence,
            "device_type": device_type,
            "visitor_found": visitor_found,
            "device_info": {
                "device": browser_details.get("device", ""),
                "os": browser_details.get("os", ""),
                "os_version": browser_details.get("osVersion", ""),
            },
            "browser_info": {
                "name": browser_details.get("browserName", ""),
                "version": browser_details.get("browserMajorVersion", ""),
                "full_version": browser_details.get("browserFullVersion", ""),
                "engine": browser_details.get("browserEngine", ""),
                "incognito": visit.get("incognito", False),
            },
            "geo_info": {
                "country": ip_location.get("country", {}).get("name", ""),
                "country_code": ip_location.get("country", {}).get("code", ""),
                "city": ip_location.get("city", {}).get("name", ""),
                "latitude": ip_location.get("latitude"),
                "longitude": ip_location.get("longitude"),
                "accuracy_radius": ip_location.get("accuracyRadius"),
                "timezone": ip_location.get("timezone", ""),
            },
            "browser": browser_details.get("browserName", ""),
            "os": browser_details.get("os", ""),
            "user_agent": browser_details.get("userAgent", ""),
            "ip_address": visit.get("ip"),
        }

        context_data = {
            "request_id": payload.get("requestId", ""),
            "timestamp": visit.get("timestamp"),
            "url": visit.get("url", ""),
            "event_type": "page_view",
            "page_url": visit.get("url"),
        }

        return fingerprint_data, context_data

    # ── Device Classification ────────────────────────────────────────

    @staticmethod
    def classify_device_type(browser_details: dict) -> str:
        """
        Classify device type from FingerprintJS browser details.

        Returns: "mobile", "tablet", "desktop", or "unknown"
        """
        device = browser_details.get("device", "").lower()

        if "mobile" in device or "phone" in device:
            return "mobile"
        elif "tablet" in device or "ipad" in device:
            return "tablet"
        elif "desktop" in device or "pc" in device:
            return "desktop"

        # Fallback: check OS
        os_name = browser_details.get("os", "").lower()
        if os_name in ("android", "ios"):
            return "mobile"
        elif os_name in ("windows", "macos", "linux"):
            return "desktop"

        return "unknown"

    # ── Datetime Parsing ─────────────────────────────────────────────

    @staticmethod
    def parse_datetime(datetime_str: str) -> Optional[datetime]:
        """Parse ISO format datetime string from FingerprintJS."""
        if not datetime_str:
            return None
        try:
            # Handle Z suffix
            clean = datetime_str.replace("Z", "+00:00")
            return datetime.fromisoformat(clean)
        except (ValueError, TypeError):
            logger.warning("Failed to parse datetime: %s", datetime_str)
            return None

    # ── Visit Data Extraction ────────────────────────────────────────

    @classmethod
    def extract_all_visits_data(cls, payload: dict) -> list[dict]:
        """
        Extract data from all visits in a FingerprintJS payload.

        Returns:
            List of visit info dicts.
        """
        visits = payload.get("visits", [])
        result = []

        for visit in visits:
            result.append(
                {
                    "timestamp": visit.get("timestamp"),
                    "url": visit.get("url"),
                    "ip": visit.get("ip"),
                    "incognito": visit.get("incognito", False),
                    "browser": visit.get("browserDetails", {}).get("browserName", ""),
                    "os": visit.get("browserDetails", {}).get("os", ""),
                }
            )

        return result

    # ── Fraud Detection ──────────────────────────────────────────────

    @classmethod
    def detect_fraud_patterns(cls, fingerprint_data: dict) -> list[dict]:
        """
        Analyze fingerprint data for fraud indicators.

        Checks:
        - Incognito mode
        - Low confidence score
        - Timezone mismatch (geo vs browser)

        Returns:
            List of fraud signal dicts with type, severity, description.
        """
        signals = []

        # Incognito detection
        if fingerprint_data.get("browser_info", {}).get("incognito", False):
            signals.append(
                {
                    "type": "incognito",
                    "severity": "medium",
                    "description": "User is in incognito/private browsing mode",
                }
            )

        # Low confidence
        confidence = fingerprint_data.get("confidence_score", 0.0)
        if confidence < 0.5:
            signals.append(
                {
                    "type": "low_confidence",
                    "severity": "high",
                    "description": f"Low fingerprint confidence: {confidence}",
                }
            )

        # VPN/proxy detection via accuracy radius
        accuracy = fingerprint_data.get("geo_info", {}).get("accuracy_radius")
        if accuracy and accuracy > 1000:
            signals.append(
                {
                    "type": "vpn_suspected",
                    "severity": "high",
                    "description": f"High geo accuracy radius ({accuracy}km) suggests VPN/proxy",
                }
            )

        return signals

    @staticmethod
    def calculate_fraud_score(signals: list[dict]) -> float:
        """
        Calculate aggregate fraud score from individual signals.

        Returns: Float between 0.0 (clean) and 1.0 (definitely fraud).
        """
        weights = {"high": 0.3, "medium": 0.15, "low": 0.05}
        score = sum(weights.get(s["severity"], 0.05) for s in signals)
        return min(score, 1.0)

    @staticmethod
    def get_fraud_recommendation(fraud_score: float) -> str:
        """
        Get a fraud handling recommendation based on score.

        Returns: "block", "review", or "allow"
        """
        if fraud_score >= 0.7:
            return "block"
        elif fraud_score >= 0.4:
            return "review"
        return "allow"
