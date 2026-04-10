"""
MetaCAPIService — Meta Conversions API (CAPI) integration.

Uses the official Meta Business SDK (`facebook-business`) for server-side
conversion event delivery. This is the server-to-server complement of the
browser pixel, enabling:
- Better ad attribution (no ad blocker interference)
- Higher match quality (server-side hashed PII)
- Event deduplication with browser pixel (via event_id)

Architecture:
    CaptureService.process_lead()
      → views.py dispatches Celery task
      → send_meta_conversion.delay(...)
      → MetaCAPIService.send_lead_event()
      → facebook_business SDK → Meta Graph API /events

Reference:
    https://developers.facebook.com/docs/marketing-api/conversions-api/using-the-api

User data hashing follows Meta's normalization rules:
    - Email: lowercase, strip → SHA-256 (done by core.shared.hashing)
    - Phone: digits only → SHA-256 (done by core.shared.hashing)
    - SDK's UserData accepts pre-hashed values via `emails`/`phones` (plural) params

Event deduplication:
    Uses event_id (capture_token UUID) so browser pixel + CAPI don't double-count.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CAPIResponse:
    """Response from Meta CAPI send."""

    success: bool
    events_received: int = 0
    fbtrace_id: str = ""
    error: str = ""


class MetaCAPIService:
    """Encapsulates Meta Conversions API calls via official SDK.

    Usage:
        service = MetaCAPIService(
            pixel_id="123456789",
            access_token="EAAx...",
        )
        response = service.send_lead_event(
            email_hash="sha256...",
            phone_hash="sha256...",
            event_id="capture-token-uuid",
            event_source_url="https://example.com/inscrever-wh-rc-v3/",
            client_ip="1.2.3.4",
            user_agent="Mozilla/5.0 ...",
        )
    """

    def __init__(
        self,
        pixel_id: str,
        access_token: str,
        *,
        test_event_code: str = "",
    ) -> None:
        """Initialize MetaCAPIService.

        Args:
            pixel_id: Meta Pixel ID.
            access_token: System user access token with ads_management permission.
            test_event_code: Optional test event code for Test Events tool.
                When set, events appear in Events Manager > Test Events tab
                instead of being attributed to real campaigns.
        """
        self.pixel_id = pixel_id
        self.access_token = access_token
        self.test_event_code = test_event_code

    def _build_user_data(
        self,
        *,
        email_hash: str = "",
        phone_hash: str = "",
        client_ip: str = "",
        user_agent: str = "",
        fbc: str = "",
        fbp: str = "",
        external_id: str = "",
    ) -> Any:
        """Build SDK UserData object from hashed parameters.

        Args:
            email_hash: SHA-256 of normalized email (pre-hashed).
            phone_hash: SHA-256 of digits-only phone (pre-hashed).
            client_ip: Visitor's IP address.
            user_agent: Visitor's User-Agent header.
            fbc: _fbc cookie value (Meta click ID).
            fbp: _fbp cookie value (Meta browser ID).
            external_id: Identity public_id for cross-platform matching.

        Returns:
            facebook_business.adobjects.serverside.UserData instance.
        """
        from facebook_business.adobjects.serverside.user_data import UserData

        user_data = UserData()

        # Use plural setters (emails/phones) for pre-hashed values
        # The SDK expects arrays of pre-hashed strings
        if email_hash:
            user_data.emails = [email_hash]
        if phone_hash:
            user_data.phones = [phone_hash]
        if client_ip:
            user_data.client_ip_address = client_ip
        if user_agent:
            user_data.client_user_agent = user_agent
        if fbc:
            user_data.fbc = fbc
        if fbp:
            user_data.fbp = fbp
        if external_id:
            user_data.external_ids = [external_id]

        return user_data

    def _build_event(
        self,
        *,
        event_name: str,
        event_id: str,
        event_source_url: str = "",
        user_data: Any = None,
        custom_data: dict[str, Any] | None = None,
        event_time: int | None = None,
    ) -> Any:
        """Build SDK Event object.

        Args:
            event_name: Standard event name (Lead, PageView, etc.).
            event_id: Deduplication key (capture_token UUID).
            event_source_url: Full URL where the event occurred.
            user_data: SDK UserData instance.
            custom_data: Optional event-specific data.
            event_time: Unix timestamp (seconds). Defaults to now.

        Returns:
            facebook_business.adobjects.serverside.Event instance.
        """
        from facebook_business.adobjects.serverside.action_source import ActionSource
        from facebook_business.adobjects.serverside.event import Event

        event = Event(
            event_name=event_name,
            event_time=event_time or int(time.time()),
            event_id=event_id,
            action_source=ActionSource.WEBSITE,
        )

        if event_source_url:
            event.event_source_url = event_source_url
        if user_data is not None:
            event.user_data = user_data
        if custom_data:
            from facebook_business.adobjects.serverside.custom_data import CustomData

            cd = CustomData()
            # CustomData supports content_name, currency, value, etc.
            # For Lead events we typically don't need custom_data,
            # but it's here for future Purchase/InitiateCheckout events.
            for key, value in custom_data.items():
                if hasattr(cd, key):
                    setattr(cd, key, value)
            event.custom_data = cd

        return event

    def _send_events(self, events: list[Any]) -> CAPIResponse:
        """Send events to Meta CAPI via SDK's EventRequest.

        Args:
            events: List of SDK Event instances.

        Returns:
            CAPIResponse with success status.
        """
        if not events:
            return CAPIResponse(success=True, events_received=0)

        if not self.pixel_id or not self.access_token:
            logger.warning(
                "MetaCAPI: pixel_id or access_token not configured, skipping"
            )
            return CAPIResponse(success=False, error="not_configured")

        try:
            from facebook_business.adobjects.serverside.event_request import (
                EventRequest,
            )

            kwargs: dict[str, Any] = {
                "pixel_id": self.pixel_id,
                "events": events,
                "access_token": self.access_token,
            }
            if self.test_event_code:
                kwargs["test_event_code"] = self.test_event_code

            request = EventRequest(**kwargs)

            response = request.execute()

            events_received = getattr(response, "events_received", 0)
            fbtrace_id = getattr(response, "fbtrace_id", "")

            logger.info(
                "MetaCAPI: sent %d event(s) to pixel %s (events_received=%d, fbtrace=%s)",
                len(events),
                self.pixel_id,
                events_received,
                fbtrace_id,
            )
            return CAPIResponse(
                success=True,
                events_received=events_received,
                fbtrace_id=str(fbtrace_id),
            )

        except Exception as exc:
            error_msg = str(exc)
            logger.error(
                "MetaCAPI: error sending to pixel %s — %s",
                self.pixel_id,
                error_msg,
            )
            return CAPIResponse(success=False, error=error_msg)

    # ── Public API: high-level event methods ─────────────────────────

    def send_lead_event(
        self,
        *,
        email_hash: str,
        phone_hash: str,
        event_id: str,
        event_source_url: str = "",
        client_ip: str = "",
        user_agent: str = "",
        fbc: str = "",
        fbp: str = "",
        external_id: str = "",
        event_time: int | None = None,
    ) -> CAPIResponse:
        """Send a 'Lead' event for capture form submission.

        This is the primary event type for lead capture campaigns.
        Maps 1:1 to a successful form submission on /inscrever-{slug}/.

        Args:
            email_hash: SHA-256 of normalized email.
            phone_hash: SHA-256 of digits-only phone.
            event_id: Deduplication key (capture_token UUID).
            event_source_url: Full URL of the capture page.
            client_ip: Visitor's IP address.
            user_agent: Visitor's User-Agent header.
            fbc: _fbc cookie value (Meta click ID).
            fbp: _fbp cookie value (Meta browser ID).
            external_id: Identity public_id (for cross-platform matching).
            event_time: Unix timestamp. Defaults to now.

        Returns:
            CAPIResponse with success status.
        """
        user_data = self._build_user_data(
            email_hash=email_hash,
            phone_hash=phone_hash,
            client_ip=client_ip,
            user_agent=user_agent,
            fbc=fbc,
            fbp=fbp,
            external_id=external_id,
        )

        event = self._build_event(
            event_name="Lead",
            event_id=event_id,
            event_source_url=event_source_url,
            user_data=user_data,
            event_time=event_time,
        )

        return self._send_events([event])

    def send_page_view_event(
        self,
        *,
        event_id: str,
        event_source_url: str = "",
        client_ip: str = "",
        user_agent: str = "",
        fbc: str = "",
        fbp: str = "",
        external_id: str = "",
        event_time: int | None = None,
    ) -> CAPIResponse:
        """Send a 'PageView' event for landing page load.

        Useful for PageView deduplication with browser pixel.

        Args:
            event_id: Deduplication key (capture_token UUID).
            event_source_url: Full URL of the page.
            client_ip: Visitor's IP address.
            user_agent: Visitor's User-Agent header.
            fbc: _fbc cookie value.
            fbp: _fbp cookie value.
            external_id: Identity public_id.
            event_time: Unix timestamp. Defaults to now.

        Returns:
            CAPIResponse with success status.
        """
        user_data = self._build_user_data(
            client_ip=client_ip,
            user_agent=user_agent,
            fbc=fbc,
            fbp=fbp,
            external_id=external_id,
        )

        event = self._build_event(
            event_name="PageView",
            event_id=event_id,
            event_source_url=event_source_url,
            user_data=user_data,
            event_time=event_time,
        )

        return self._send_events([event])
