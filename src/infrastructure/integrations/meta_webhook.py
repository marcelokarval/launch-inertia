"""
Meta CAPI Webhook — receives test event verification from Meta.

Meta's Events Manager can send test pings to verify server connectivity.
This endpoint handles:
1. GET with hub.challenge — Meta webhook verification handshake
2. POST with event data — Acknowledgement (log only, no processing)

This is NOT for receiving conversion events FROM Meta. It's for Meta
to verify that our server is reachable and correctly configured.

URL: /api/webhooks/meta/
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
from typing import Any

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def meta_webhook(request: HttpRequest) -> HttpResponse:
    """Meta webhook endpoint for verification and test events.

    GET: Webhook verification handshake.
        Meta sends: hub.mode=subscribe, hub.challenge=<string>, hub.verify_token=<token>
        We respond with hub.challenge if verify_token matches.

    POST: Event notification (test events or real webhook events).
        We verify the X-Hub-Signature-256 header, log the payload,
        and return 200 OK.
    """
    if request.method == "GET":
        return _handle_verification(request)
    return _handle_event(request)


def _handle_verification(request: HttpRequest) -> HttpResponse:
    """Handle Meta webhook verification (GET).

    Meta sends a GET request with:
    - hub.mode: "subscribe"
    - hub.challenge: random string Meta expects back
    - hub.verify_token: our pre-shared verify token

    We must respond with the hub.challenge value (plain text)
    if the verify_token matches.
    """
    mode = request.GET.get("hub.mode", "")
    challenge = request.GET.get("hub.challenge", "")
    verify_token = request.GET.get("hub.verify_token", "")

    expected_token = os.getenv("META_WEBHOOK_VERIFY_TOKEN", "")

    if mode == "subscribe" and verify_token and verify_token == expected_token:
        logger.info("Meta webhook verification successful")
        return HttpResponse(challenge, content_type="text/plain")

    logger.warning(
        "Meta webhook verification failed (mode=%s, token_match=%s)",
        mode,
        verify_token == expected_token,
    )
    return HttpResponse("Verification failed", status=403)


def _handle_event(request: HttpRequest) -> HttpResponse:
    """Handle Meta webhook event notification (POST).

    Verifies the X-Hub-Signature-256 header using the app secret,
    then logs the event payload. We don't process these events —
    they're informational (test pings, delivery status, etc.).
    """
    # Verify signature
    app_secret = os.getenv("META_APP_SECRET", "")
    if app_secret:
        signature_header = request.META.get("HTTP_X_HUB_SIGNATURE_256", "")
        if not _verify_signature(request.body, app_secret, signature_header):
            logger.warning("Meta webhook: invalid signature")
            return JsonResponse({"error": "invalid_signature"}, status=403)

    # Parse and log payload
    try:
        payload: dict[str, Any] = json.loads(request.body) if request.body else {}
        entry = payload.get("entry", [])
        logger.info(
            "Meta webhook event received: object=%s, entries=%d",
            payload.get("object", "unknown"),
            len(entry),
        )
    except (json.JSONDecodeError, UnicodeDecodeError):
        logger.warning("Meta webhook: invalid JSON payload")
        return JsonResponse({"error": "invalid_json"}, status=400)

    # Always return 200 to acknowledge receipt
    return JsonResponse({"status": "ok"})


def _verify_signature(
    payload: bytes,
    app_secret: str,
    signature_header: str,
) -> bool:
    """Verify X-Hub-Signature-256 header.

    Meta signs webhook payloads with HMAC-SHA256 using the app secret.
    Header format: "sha256=<hex_digest>"

    Uses hmac.compare_digest for timing-attack resistance.
    """
    if not signature_header or not signature_header.startswith("sha256="):
        return False

    expected_signature = signature_header[len("sha256=") :]
    computed = hmac.new(
        app_secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(computed, expected_signature)
