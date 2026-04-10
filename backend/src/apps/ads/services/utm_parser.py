"""
UTMParserService — parse pipe-separated UTMs and resolve ad dimensions.

Auto-detects provider from AdProvider.source_patterns, loads naming_convention,
applies split_with_fallback, and get_or_create all dimension records.

Resilient: if parsing fails, raw data is preserved in parsed_data._raw
for re-processing when naming conventions are updated.

See CAPTURE_DATA_ARCHITECTURE.md section 6 for full architecture.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Optional

from apps.ads.models import (
    AdCampaign,
    AdCreative,
    AdGroup,
    AdPlatform,
    AdProvider,
    TrafficSource,
)

logger = logging.getLogger(__name__)


@dataclass
class ParsedUTMResult:
    """Result of UTM parsing with resolved dimension FKs."""

    provider: Optional[AdProvider] = None
    traffic_source: Optional[TrafficSource] = None
    campaign: Optional[AdCampaign] = None
    ad_group: Optional[AdGroup] = None
    creative: Optional[AdCreative] = None
    click_id: str = ""
    raw_utms: dict[str, str] = field(default_factory=dict)


# ── Mapping tables ───────────────────────────────────────────────────

# Portuguese -> normalized values
_PAYMENT_TYPE_MAP: dict[str, str] = {
    "pago": "paid",
    "paid": "paid",
    "organico": "organic",
    "organic": "organic",
}

_TEMPERATURE_MAP: dict[str, str] = {
    "quente": "hot",
    "hot": "hot",
    "frio": "cold",
    "cold": "cold",
    "morno": "warm",
    "warm": "warm",
}

_FUNNEL_STAGE_MAP: dict[str, str] = {
    "captacao": "capture",
    "captação": "capture",
    "capture": "capture",
    "capt": "capture",
    "vendas": "sales",
    "sales": "sales",
    "checkout": "checkout",
    "conteudo": "content",
    "conteúdo": "content",
    "content": "content",
    "retencao": "retention",
    "retenção": "retention",
    "retention": "retention",
}

# Interest code -> slug mapping (from utm_content creative codes)
_INTEREST_CODE_MAP: dict[str, str] = {
    "rc": "rc",
    "td": "td",
    "ds": "ds",
    "cp": "cp",
    "bf": "bf",
}


class UTMParserService:
    """Parse UTM parameters and resolve to normalized ad dimensions."""

    @classmethod
    def parse(
        cls,
        utm_data: dict[str, str],
        extra_params: dict[str, str] | None = None,
        *,
        launch: Any = None,
    ) -> ParsedUTMResult:
        """Parse UTM data and get_or_create all dimension records.

        Args:
            utm_data: Standard UTM parameters (utm_source, utm_medium, etc.).
            extra_params: Additional params (fbclid, vk_ad_id, vk_source).
            launch: Optional Launch instance for campaign FK.

        Returns:
            ParsedUTMResult with resolved dimensions.
        """
        extra_params = extra_params or {}
        result = ParsedUTMResult(raw_utms={**utm_data, **extra_params})

        # 1. Auto-detect provider
        provider = cls._detect_provider(utm_data, extra_params)
        if provider is None:
            logger.debug("No provider detected for UTMs: %s", utm_data)
            return result
        result.provider = provider

        # 2. Extract click_id
        click_id_param = provider.source_patterns.get("click_id_param", "")
        if click_id_param:
            result.click_id = extra_params.get(click_id_param, "")
        # Fallback: check common click_id params
        if not result.click_id:
            for param in ("fbclid", "gclid", "ttclid"):
                val = extra_params.get(param, "")
                if val:
                    result.click_id = val
                    break

        # 3. Load naming convention
        convention = provider.naming_convention or {}

        # 4. Resolve traffic source (utm_source -> platform + placement)
        result.traffic_source = cls._resolve_traffic_source(
            utm_data.get("utm_source", ""), provider
        )

        # 5. Parse campaign (utm_campaign)
        result.campaign = cls._resolve_campaign(
            utm_data.get("utm_campaign", ""),
            convention,
            provider,
            launch=launch,
        )

        # 6. Parse ad group (utm_medium)
        result.ad_group = cls._resolve_ad_group(
            utm_data.get("utm_medium", ""),
            utm_data.get("utm_term", ""),
            convention,
            result.campaign,
        )

        # 7. Parse creative (utm_content + vk_ad_id)
        result.creative = cls._resolve_creative(
            utm_data.get("utm_content", ""),
            extra_params.get("vk_ad_id", ""),
            convention,
            provider,
        )

        return result

    # ── Provider detection ───────────────────────────────────────────

    @classmethod
    def _detect_provider(
        cls,
        utm_data: dict[str, str],
        extra_params: dict[str, str],
    ) -> Optional[AdProvider]:
        """Auto-detect provider based on UTM parameters.

        Priority: source_patterns regex > vk_source > click_id_param > "direct".
        """
        utm_source = utm_data.get("utm_source", "")

        try:
            providers = list(AdProvider.objects.all())
        except Exception:
            logger.exception("Failed to load AdProvider records")
            return None

        for provider in providers:
            if provider.code in ("organic", "direct"):
                continue  # Check specific providers first

            patterns = provider.source_patterns or {}

            # Check utm_source against regex patterns
            for pattern in patterns.get("utm_source_patterns", []):
                try:
                    if re.match(pattern, utm_source, re.IGNORECASE):
                        return provider
                except re.error:
                    logger.warning("Invalid regex pattern: %s", pattern)

            # Check vk_source
            vk_source = extra_params.get("vk_source", "")
            if vk_source and vk_source in patterns.get("vk_source_values", []):
                return provider

            # Check presence of provider-specific click_id
            click_param = patterns.get("click_id_param", "")
            if click_param and extra_params.get(click_param):
                return provider

        # Fallback: organic if has utm_source, else direct
        if utm_source:
            return AdProvider.objects.filter(code="organic").first()
        return AdProvider.objects.filter(code="direct").first()

    # ── Traffic source resolution ────────────────────────────────────

    @classmethod
    def _resolve_traffic_source(
        cls,
        utm_source: str,
        provider: AdProvider,
    ) -> Optional[TrafficSource]:
        """Resolve utm_source to TrafficSource dimension.

        utm_source="Instagram_Reels" -> platform=instagram, placement=reels.
        """
        if not utm_source:
            return None

        # Try splitting by underscore (Meta pattern: Platform_Placement)
        parts = utm_source.split("_", 1)
        platform_code = parts[0].lower().strip()
        placement = parts[1].lower().strip() if len(parts) > 1 else "feed"

        # Find or approximate platform
        platform = AdPlatform.objects.filter(code=platform_code).first()
        if platform is None:
            # Try matching against known platform codes
            platform = AdPlatform.objects.filter(code__icontains=platform_code).first()

        if platform is None:
            # Create "unknown" platform under this provider
            platform, _ = AdPlatform.objects.get_or_create(
                code=platform_code,
                defaults={
                    "provider": provider,
                    "name": platform_code.title(),
                    "platform_data": {"auto_created": True},
                },
            )

        # Validate placement against known placements
        valid_placements = (
            platform.platform_data.get("valid_placements", [])
            if platform.platform_data
            else []
        )
        if valid_placements and placement not in valid_placements:
            placement = platform.platform_data.get("default_placement", placement)

        traffic_source, _ = TrafficSource.objects.get_or_create(
            platform=platform,
            placement=placement,
        )
        return traffic_source

    # ── Campaign resolution ──────────────────────────────────────────

    @classmethod
    def _resolve_campaign(
        cls,
        utm_campaign: str,
        convention: dict[str, Any],
        provider: AdProvider,
        *,
        launch: Any = None,
    ) -> Optional[AdCampaign]:
        """Parse utm_campaign and get_or_create AdCampaign."""
        if not utm_campaign:
            return None

        separator = convention.get("utm_campaign_separator", "|")
        segments = convention.get(
            "utm_campaign_segments",
            ["launch_code", "campaign_name", "campaign_provider_id"],
        )
        parsed = cls._split_with_fallback(utm_campaign, separator, segments)

        external_id = parsed.get("campaign_provider_id", "")
        campaign_name = parsed.get("campaign_name", utm_campaign)
        launch_code = parsed.get("launch_code", "")

        # Extract funnel stage from campaign name
        funnel_stage = cls._extract_funnel_stage(campaign_name)

        # Resolve launch FK if we have launch_code and no explicit launch
        resolved_launch = launch
        if not resolved_launch and launch_code:
            from apps.launches.models import Launch

            resolved_launch = Launch.objects.filter(
                launch_code__iexact=launch_code
            ).first()

        # Resolve interest from campaign name
        interest = cls._extract_interest_from_name(campaign_name)

        # Build lookup and defaults
        if external_id:
            campaign_obj, _ = AdCampaign.objects.get_or_create(
                provider=provider,
                external_id=external_id,
                defaults={
                    "name": campaign_name or utm_campaign,
                    "launch": resolved_launch,
                    "interest": interest,
                    "funnel_stage": funnel_stage,
                    "parsed_data": parsed,
                },
            )
        else:
            campaign_obj, _ = AdCampaign.objects.get_or_create(
                provider=provider,
                name=campaign_name or utm_campaign,
                launch=resolved_launch,
                defaults={
                    "external_id": "",
                    "interest": interest,
                    "funnel_stage": funnel_stage,
                    "parsed_data": parsed,
                },
            )

        return campaign_obj

    # ── Ad group resolution ──────────────────────────────────────────

    @classmethod
    def _resolve_ad_group(
        cls,
        utm_medium: str,
        utm_term: str,
        convention: dict[str, Any],
        campaign: Optional[AdCampaign],
    ) -> Optional[AdGroup]:
        """Parse utm_medium and get_or_create AdGroup."""
        if not utm_medium or campaign is None:
            return None

        separator = convention.get("utm_medium_separator", "|")
        segments = convention.get(
            "utm_medium_segments",
            ["payment_type", "audience_temp", "adgroup_name", "adgroup_provider_id"],
        )
        parsed = cls._split_with_fallback(utm_medium, separator, segments)

        # Normalize payment_type and temperature
        raw_payment = parsed.get("payment_type", "").lower().strip()
        payment_type = _PAYMENT_TYPE_MAP.get(raw_payment, "paid")

        raw_temp = parsed.get("audience_temp", "").lower().strip()
        audience_temperature = _TEMPERATURE_MAP.get(raw_temp, "")

        adgroup_name = parsed.get("adgroup_name", utm_medium)
        external_id = parsed.get("adgroup_provider_id", "")

        # Fallback: utm_term often has the Meta Adset ID
        if not external_id and utm_term:
            fallback_param = convention.get("adset_id_fallback", "utm_term")
            if fallback_param == "utm_term":
                external_id = utm_term

        if external_id:
            ad_group, _ = AdGroup.objects.get_or_create(
                campaign=campaign,
                external_id=external_id,
                defaults={
                    "name": adgroup_name or utm_medium,
                    "payment_type": payment_type,
                    "audience_temperature": audience_temperature,
                    "parsed_data": parsed,
                },
            )
        else:
            ad_group, _ = AdGroup.objects.get_or_create(
                campaign=campaign,
                name=adgroup_name or utm_medium,
                defaults={
                    "external_id": "",
                    "payment_type": payment_type,
                    "audience_temperature": audience_temperature,
                    "parsed_data": parsed,
                },
            )

        return ad_group

    # ── Creative resolution ──────────────────────────────────────────

    @classmethod
    def _resolve_creative(
        cls,
        utm_content: str,
        vk_ad_id: str,
        convention: dict[str, Any],
        provider: AdProvider,
    ) -> Optional[AdCreative]:
        """Parse utm_content and get_or_create AdCreative."""
        if not utm_content and not vk_ad_id:
            return None

        separator = convention.get("utm_content_separator", "_")
        segments = convention.get(
            "utm_content_segments",
            ["creative_seq", "interest_code", "funnel_stage", "creative_launch_code"],
        )

        parsed = {}
        creative_code = ""
        full_code = utm_content or ""
        funnel_stage = ""
        original_launch_code = ""
        interest = None

        if utm_content:
            parsed = cls._split_with_fallback(utm_content, separator, segments)

            creative_seq = parsed.get("creative_seq", "")
            creative_code = creative_seq  # e.g., "AD364"

            interest_code = parsed.get("interest_code", "").lower()
            if interest_code in _INTEREST_CODE_MAP:
                interest = cls._get_interest_by_slug(_INTEREST_CODE_MAP[interest_code])

            raw_stage = parsed.get("funnel_stage", "").lower()
            funnel_stage = _FUNNEL_STAGE_MAP.get(raw_stage, raw_stage)

            original_launch_code = parsed.get("creative_launch_code", "")

        # Lookup: prefer external_id (vk_ad_id), fallback to full_code
        if vk_ad_id:
            creative, _ = AdCreative.objects.get_or_create(
                provider=provider,
                external_id=vk_ad_id,
                defaults={
                    "creative_code": creative_code,
                    "full_code": full_code,
                    "original_interest": interest,
                    "original_launch_code": original_launch_code,
                    "funnel_stage": funnel_stage,
                    "provider_data": parsed,
                },
            )
        elif full_code:
            creative, _ = AdCreative.objects.get_or_create(
                provider=provider,
                full_code=full_code,
                external_id="",
                defaults={
                    "creative_code": creative_code,
                    "original_interest": interest,
                    "original_launch_code": original_launch_code,
                    "funnel_stage": funnel_stage,
                    "provider_data": parsed,
                },
            )
        else:
            return None

        return creative

    # ── Helper methods ───────────────────────────────────────────────

    @staticmethod
    def _split_with_fallback(
        value: str, separator: str, expected_segments: list[str]
    ) -> dict[str, Any]:
        """Split pipe-separated value. Fallback to raw if mismatch.

        If parsing fails, the data is NOT lost — stored in _raw for
        re-processing when naming conventions are updated.
        """
        if not value or separator not in value:
            return {"_raw": value}

        parts = value.split(separator)
        if len(parts) >= len(expected_segments):
            result = dict(zip(expected_segments, parts[: len(expected_segments)]))
            if len(parts) > len(expected_segments):
                result["_extra_segments"] = parts[len(expected_segments) :]  # type: ignore[assignment]
            return result

        # Fallback: could not parse, store raw
        return {
            "_raw": value,
            "_parse_error": (
                f"expected {len(expected_segments)} segments, got {len(parts)}"
            ),
        }

    @staticmethod
    def _extract_funnel_stage(campaign_name: str) -> str:
        """Extract funnel stage from campaign name brackets."""
        name_lower = campaign_name.lower()
        for key, stage in _FUNNEL_STAGE_MAP.items():
            if f"[{key}]" in name_lower or key in name_lower:
                return stage
        return ""

    @staticmethod
    def _extract_interest_from_name(campaign_name: str) -> Any:
        """Extract Interest FK from campaign name bracket patterns."""
        # Look for patterns like [Repasse], [Tax Deed], [Do Zero]
        bracket_pattern = re.findall(r"\[([^\]]+)\]", campaign_name)
        if not bracket_pattern:
            return None

        from apps.launches.models import Interest

        for bracket_content in bracket_pattern:
            content_lower = bracket_content.lower().strip()
            # Try direct slug match
            interest = Interest.objects.filter(slug__icontains=content_lower).first()
            if interest:
                return interest
            # Try name match
            interest = Interest.objects.filter(name__icontains=content_lower).first()
            if interest:
                return interest

        return None

    @staticmethod
    def _get_interest_by_slug(slug_fragment: str) -> Any:
        """Get Interest by slug fragment (rc, td, ds, etc.)."""
        from apps.launches.models import Interest

        return Interest.objects.filter(slug__icontains=slug_fragment).first()
