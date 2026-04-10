"""
Base classes for external API integrations.
"""
import logging
from typing import Any, Dict, Optional
from dataclasses import dataclass
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


@dataclass
class APIResponse:
    """Standardized API response."""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    status_code: Optional[int] = None


class BaseAPIClient:
    """
    Base class for external API clients.

    Provides:
    - Automatic retries
    - Timeout handling
    - Error standardization
    - Request/response logging

    Usage:
        class StripeClient(BaseAPIClient):
            BASE_URL = "https://api.stripe.com/v1"

            def __init__(self, api_key: str):
                super().__init__()
                self.session.headers["Authorization"] = f"Bearer {api_key}"

            def create_customer(self, email: str) -> APIResponse:
                return self.post("/customers", data={"email": email})
    """

    BASE_URL: str = ""
    TIMEOUT: int = 30
    MAX_RETRIES: int = 3

    def __init__(self):
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create session with retry configuration."""
        session = requests.Session()

        retry_strategy = Retry(
            total=self.MAX_RETRIES,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _build_url(self, endpoint: str) -> str:
        """Build full URL from endpoint."""
        if endpoint.startswith("http"):
            return endpoint
        return f"{self.BASE_URL.rstrip('/')}/{endpoint.lstrip('/')}"

    def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> APIResponse:
        """Make HTTP request with error handling."""
        url = self._build_url(endpoint)
        kwargs.setdefault("timeout", self.TIMEOUT)

        try:
            response = self.session.request(method, url, **kwargs)

            logger.debug(
                f"API {method} {url} -> {response.status_code}",
                extra={"status_code": response.status_code}
            )

            # Try to parse JSON response
            try:
                data = response.json()
            except ValueError:
                data = response.text

            if response.ok:
                return APIResponse(
                    success=True,
                    data=data,
                    status_code=response.status_code
                )
            else:
                error_msg = data if isinstance(data, str) else data.get("error", str(data))
                return APIResponse(
                    success=False,
                    error=error_msg,
                    status_code=response.status_code,
                    data=data
                )

        except requests.Timeout:
            logger.error(f"API timeout: {method} {url}")
            return APIResponse(success=False, error="Request timeout")

        except requests.ConnectionError:
            logger.error(f"API connection error: {method} {url}")
            return APIResponse(success=False, error="Connection error")

        except Exception as e:
            logger.exception(f"API error: {method} {url}")
            return APIResponse(success=False, error=str(e))

    def get(self, endpoint: str, params: Optional[Dict] = None, **kwargs) -> APIResponse:
        """HTTP GET request."""
        return self._request("GET", endpoint, params=params, **kwargs)

    def post(self, endpoint: str, data: Optional[Dict] = None, json: Optional[Dict] = None, **kwargs) -> APIResponse:
        """HTTP POST request."""
        return self._request("POST", endpoint, data=data, json=json, **kwargs)

    def put(self, endpoint: str, data: Optional[Dict] = None, json: Optional[Dict] = None, **kwargs) -> APIResponse:
        """HTTP PUT request."""
        return self._request("PUT", endpoint, data=data, json=json, **kwargs)

    def patch(self, endpoint: str, data: Optional[Dict] = None, json: Optional[Dict] = None, **kwargs) -> APIResponse:
        """HTTP PATCH request."""
        return self._request("PATCH", endpoint, data=data, json=json, **kwargs)

    def delete(self, endpoint: str, **kwargs) -> APIResponse:
        """HTTP DELETE request."""
        return self._request("DELETE", endpoint, **kwargs)
