"""
N8N webhook proxy service.

Django acts as intermediary between the capture form and N8N.
The legacy system POSTed directly from the browser; now Django
validates, resolves identity, then forwards to N8N asynchronously via Celery.
"""

import logging
from datetime import datetime, timezone
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# Timeout for N8N webhook calls
_N8N_TIMEOUT = 15.0
_N8N_MAX_RETRIES = 3


class N8NProxyService:
    """Proxy service for forwarding lead data to N8N webhooks."""

    @classmethod
    def build_n8n_payload(
        cls,
        *,
        email: str,
        phone: str,
        visitor_id: str,
        request_id: str,
        utm_data: dict[str, str],
        campaign_config: dict[str, Any],
        page_url: str = "",
        referrer: str = "",
    ) -> dict[str, Any]:
        """Build the N8N-compatible payload matching legacy format.

        The N8N workflows expect specific field names (e.g., "E-mail" with
        capital E and hyphen for ActiveCampaign compatibility).
        """
        n8n_config = campaign_config.get("n8n", {})

        return {
            # Contact fields (ActiveCampaign naming convention)
            "E-mail": email,
            "phone": phone,
            # UTM tracking (with _cp suffix for ActiveCampaign)
            "utm_source_cp": utm_data.get("utm_source", ""),
            "utm_medium_cp": utm_data.get("utm_medium", ""),
            "utm_campaign_cp": utm_data.get("utm_campaign", ""),
            "utm_content_cp": utm_data.get("utm_content", ""),
            "utm_term_cp": utm_data.get("utm_term", ""),
            "utm_id": utm_data.get("utm_id", ""),
            # Page/campaign metadata
            "versao_page_cp": campaign_config.get("slug", ""),
            "versao_copy_cp": "",
            "interesse_lead_cp": "",
            # Origin tracking
            "origem_lead_cp": page_url,
            "origem_lead_history_1": referrer,
            "origem_lead_history_2": "",
            # Fingerprint data (CRITICAL for N8N workflows)
            "fingerprint": visitor_id,
            "eventid": request_id,
            # Campaign identifiers
            "list": n8n_config.get("list_id", ""),
            "launch_code": n8n_config.get("launch_code", ""),
            "form_id": n8n_config.get("form_id", ""),
            "form_name": n8n_config.get("form_name", ""),
            # Timestamp
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @classmethod
    def send_to_n8n(
        cls,
        webhook_url: str,
        payload: dict[str, Any],
        *,
        max_retries: int = _N8N_MAX_RETRIES,
    ) -> bool:
        """Send payload to N8N webhook with retry logic.

        Args:
            webhook_url: The N8N webhook URL.
            payload: The JSON payload to send.
            max_retries: Maximum retry attempts.

        Returns:
            True if the webhook accepted the payload, False otherwise.
        """
        if not webhook_url:
            logger.warning("N8N webhook URL is empty, skipping send")
            return False

        last_error: Exception | None = None

        for attempt in range(max_retries):
            try:
                with httpx.Client(timeout=_N8N_TIMEOUT) as client:
                    response = client.post(
                        webhook_url,
                        json=payload,
                        headers={"Content-Type": "application/json"},
                    )
                    response.raise_for_status()

                logger.info(
                    "N8N webhook sent successfully (attempt %d): %s",
                    attempt + 1,
                    webhook_url,
                )
                return True

            except httpx.HTTPStatusError as exc:
                last_error = exc
                logger.warning(
                    "N8N webhook HTTP error (attempt %d/%d): %s - %s",
                    attempt + 1,
                    max_retries,
                    exc.response.status_code,
                    webhook_url,
                )
            except (httpx.ConnectError, httpx.TimeoutException) as exc:
                last_error = exc
                logger.warning(
                    "N8N webhook connection error (attempt %d/%d): %s - %s",
                    attempt + 1,
                    max_retries,
                    type(exc).__name__,
                    webhook_url,
                )

        logger.error(
            "N8N webhook failed after %d attempts: %s - %s",
            max_retries,
            webhook_url,
            last_error,
        )
        return False
