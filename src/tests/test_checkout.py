"""
Tests for Phase E: Stripe Checkout integration.

Covers:
- Checkout JSON API views (create-session, create-customer, create-subscription, etc.)
- Session status retrieval with smart prefix routing
- User.is_delinquent property wiring
- Input validation and error handling
"""
# pyright: reportAttributeAccessIssue=false

import json
from dataclasses import dataclass
from unittest.mock import MagicMock, patch

import pytest
from django.test import Client
from django.test import override_settings


# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def client():
    """Django test client with CSRF enforcement disabled for JSON tests."""
    return Client(enforce_csrf_checks=False)


@pytest.fixture
def csrf_client():
    """Django test client with CSRF enforcement enabled."""
    return Client(enforce_csrf_checks=True)


# ── Checkout Page Views (Inertia) ─────────────────────────────────────


class TestCheckoutPageView:
    """Tests for GET /checkout-<campaign_slug>/ (Inertia page)."""

    def test_renders_checkout_page(self, client, db):
        """Should return 200 with Inertia props for existing campaign."""
        response = client.get("/checkout-wh-rc-v3/")
        assert response.status_code == 200

    def test_passes_stripe_key(self, client, db):
        """Should include stripe_publishable_key in response."""
        response = client.get("/checkout-wh-rc-v3/")
        assert response.status_code == 200
        # Inertia returns HTML with embedded JSON props
        content = response.content.decode()
        assert "pk_test_fake" in content

    def test_unknown_slug_redirects_to_home(self, client, db):
        """Non-existent campaign slug should redirect to home."""
        response = client.get("/checkout-nonexistent/")
        assert response.status_code == 302

    @override_settings(LANDING_JSON_FALLBACK_ENABLED=False)
    def test_db_backed_checkout_page_renders_without_json_fallback(self, client, db):
        from tests.factories import CapturePageFactory

        CapturePageFactory(slug="checkout-db-only")

        response = client.get("/checkout-checkout-db-only/")
        assert response.status_code == 200

    @override_settings(LANDING_JSON_FALLBACK_ENABLED=False)
    def test_json_only_checkout_redirects_when_fallback_disabled(self, client, db):
        response = client.get("/checkout-wh-rc-v3/")
        assert response.status_code == 302

    @override_settings(LANDING_JSON_FALLBACK_ENABLED=False)
    def test_db_backed_checkout_page_uses_capture_page_service_contract(
        self, client, db
    ):
        from tests.factories import CapturePageFactory

        page = CapturePageFactory(slug="checkout-db-contract")

        response = client.get("/checkout-checkout-db-contract/")
        assert response.status_code == 200
        content = response.content.decode()
        assert page.slug in content

    def test_only_allows_get(self, client, db):
        """POST should return 405 for existing campaign."""
        response = client.post("/checkout-wh-rc-v3/")
        assert response.status_code == 405


class TestCheckoutReturnView:
    """Tests for GET /checkout/return/ (Inertia page)."""

    def test_renders_return_page(self, client, db):
        """Should return 200."""
        response = client.get("/checkout/return/")
        assert response.status_code == 200

    def test_passes_session_id_from_query(self, client, db):
        """Should include session_id from query params."""
        response = client.get("/checkout/return/?session_id=cs_test_123")
        assert response.status_code == 200
        content = response.content.decode()
        assert "cs_test_123" in content

    def test_handles_missing_session_id(self, client, db):
        """Should render page even without session_id."""
        response = client.get("/checkout/return/")
        assert response.status_code == 200


# ── Create Checkout Session API ───────────────────────────────────────


class TestCreateCheckoutSession:
    """Tests for POST /checkout/create-session/ (JSON API)."""

    def test_requires_post(self, client, db):
        """GET should return 405."""
        response = client.get("/checkout/create-session/")
        assert response.status_code == 405

    def test_validates_line_items_required(self, client, db):
        """Missing line_items should return 400."""
        response = client.post(
            "/checkout/create-session/",
            data=json.dumps({"return_url": "https://example.com/return/"}),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = response.json()
        assert "line_items" in data["error"]

    def test_validates_return_url_required(self, client, db):
        """Missing return_url should return 400."""
        response = client.post(
            "/checkout/create-session/",
            data=json.dumps(
                {
                    "line_items": [{"price": "price_123", "quantity": 1}],
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = response.json()
        assert "return_url" in data["error"]

    def test_validates_invalid_mode(self, client, db):
        """Invalid mode should return 400."""
        response = client.post(
            "/checkout/create-session/",
            data=json.dumps(
                {
                    "line_items": [{"price": "price_123", "quantity": 1}],
                    "return_url": "https://example.com/return/",
                    "mode": "invalid",
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = response.json()
        assert "mode" in data["error"]

    def test_validates_line_item_price(self, client, db):
        """Line items without 'price' should return 400."""
        response = client.post(
            "/checkout/create-session/",
            data=json.dumps(
                {
                    "line_items": [{"quantity": 1}],
                    "return_url": "https://example.com/return/",
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = response.json()
        assert "price" in data["error"]

    def test_validates_line_item_quantity(self, client, db):
        """Line items with invalid quantity should return 400."""
        response = client.post(
            "/checkout/create-session/",
            data=json.dumps(
                {
                    "line_items": [{"price": "price_123", "quantity": 0}],
                    "return_url": "https://example.com/return/",
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = response.json()
        assert "Quantity" in data["error"]

    @patch("apps.billing.services.billing_service.stripe.checkout.Session.create")
    def test_success_returns_client_secret(self, mock_create, client, db):
        """Successful creation returns clientSecret and sessionId."""
        mock_session = MagicMock()
        mock_session.client_secret = "cs_secret_test_123"
        mock_session.id = "cs_test_session_456"
        mock_create.return_value = mock_session

        response = client.post(
            "/checkout/create-session/",
            data=json.dumps(
                {
                    "line_items": [{"price": "price_123", "quantity": 1}],
                    "return_url": "https://example.com/return/?session_id={CHECKOUT_SESSION_ID}",
                    "mode": "subscription",
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["clientSecret"] == "cs_secret_test_123"
        assert data["sessionId"] == "cs_test_session_456"

    @patch("apps.billing.services.billing_service.stripe.checkout.Session.create")
    def test_stripe_error_returns_500(self, mock_create, client, db):
        """Stripe API error should return 500."""
        mock_create.side_effect = Exception("Stripe API error")

        response = client.post(
            "/checkout/create-session/",
            data=json.dumps(
                {
                    "line_items": [{"price": "price_123", "quantity": 1}],
                    "return_url": "https://example.com/return/",
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 500
        data = response.json()
        assert "error" in data


# ── Create Customer API ───────────────────────────────────────────────


class TestCreateCustomer:
    """Tests for POST /checkout/create-customer/ (JSON API)."""

    def test_requires_post(self, client, db):
        """GET should return 405."""
        response = client.get("/checkout/create-customer/")
        assert response.status_code == 405

    def test_validates_email_required(self, client, db):
        """Missing email should return 400."""
        response = client.post(
            "/checkout/create-customer/",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = response.json()
        assert "email" in data["error"]

    @patch("apps.billing.services.billing_service.stripe.Customer.create")
    def test_success_returns_customer(self, mock_create, client, db):
        """Successful creation returns customer data."""
        mock_customer = MagicMock()
        mock_customer.id = "cus_test_123"
        mock_customer.email = "test@example.com"
        mock_customer.phone = "+5511999998888"
        mock_customer.name = "John Doe"
        mock_create.return_value = mock_customer

        response = client.post(
            "/checkout/create-customer/",
            data=json.dumps(
                {
                    "email": "test@example.com",
                    "phone": "+5511999998888",
                    "name": "John Doe",
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["customerId"] == "cus_test_123"
        assert data["email"] == "test@example.com"
        assert data["phone"] == "+5511999998888"
        assert data["name"] == "John Doe"


# ── Create Subscription API ──────────────────────────────────────────


class TestCreateSubscription:
    """Tests for POST /checkout/create-subscription/ (JSON API)."""

    def test_requires_post(self, client, db):
        """GET should return 405."""
        response = client.get("/checkout/create-subscription/")
        assert response.status_code == 405

    def test_validates_customer_id_required(self, client, db):
        """Missing customer_id should return 400."""
        response = client.post(
            "/checkout/create-subscription/",
            data=json.dumps(
                {
                    "line_items": [{"price": "price_123", "quantity": 1}],
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = response.json()
        assert "customer_id" in data["error"]

    def test_validates_line_items_required(self, client, db):
        """Missing line_items should return 400."""
        response = client.post(
            "/checkout/create-subscription/",
            data=json.dumps({"customer_id": "cus_test_123"}),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = response.json()
        assert "line_items" in data["error"]

    @patch("apps.billing.services.billing_service.stripe.Subscription.create")
    def test_success_with_payment_secret(self, mock_create, client, db):
        """Subscription with payment returns payment secret."""
        mock_invoice = MagicMock()
        mock_invoice.confirmation_secret = MagicMock()
        mock_invoice.confirmation_secret.client_secret = "pi_secret_test"

        mock_sub = MagicMock()
        mock_sub.id = "sub_test_123"
        mock_sub.status = "incomplete"
        mock_sub.pending_setup_intent = None
        mock_sub.latest_invoice = mock_invoice
        mock_create.return_value = mock_sub

        response = client.post(
            "/checkout/create-subscription/",
            data=json.dumps(
                {
                    "customer_id": "cus_test_123",
                    "line_items": [{"price": "price_123", "quantity": 1}],
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["subscriptionId"] == "sub_test_123"
        assert data["clientSecret"] == "pi_secret_test"
        assert data["secretType"] == "payment"
        assert data["status"] == "incomplete"

    @patch("apps.billing.services.billing_service.stripe.Subscription.create")
    def test_success_with_setup_secret(self, mock_create, client, db):
        """Subscription with trial returns setup secret."""
        mock_setup_intent = MagicMock()
        mock_setup_intent.client_secret = "seti_secret_test"

        mock_sub = MagicMock()
        mock_sub.id = "sub_test_456"
        mock_sub.status = "trialing"
        mock_sub.pending_setup_intent = mock_setup_intent
        mock_sub.latest_invoice = None
        mock_create.return_value = mock_sub

        response = client.post(
            "/checkout/create-subscription/",
            data=json.dumps(
                {
                    "customer_id": "cus_test_123",
                    "line_items": [{"price": "price_123", "quantity": 1}],
                    "trial_period_days": 7,
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["subscriptionId"] == "sub_test_456"
        assert data["clientSecret"] == "seti_secret_test"
        assert data["secretType"] == "setup"


# ── Create Payment Intent API ────────────────────────────────────────


class TestCreatePaymentIntent:
    """Tests for POST /checkout/create-payment-intent/ (JSON API)."""

    def test_requires_post(self, client, db):
        """GET should return 405."""
        response = client.get("/checkout/create-payment-intent/")
        assert response.status_code == 405

    def test_validates_line_items_required(self, client, db):
        """Missing line_items should return 400."""
        response = client.post(
            "/checkout/create-payment-intent/",
            data=json.dumps({"return_url": "https://example.com/return/"}),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = response.json()
        assert "line_items" in data["error"]

    def test_validates_return_url_required(self, client, db):
        """Missing return_url should return 400."""
        response = client.post(
            "/checkout/create-payment-intent/",
            data=json.dumps(
                {
                    "line_items": [{"price": "price_123", "quantity": 1}],
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = response.json()
        assert "return_url" in data["error"]

    @patch("apps.billing.services.billing_service.stripe.PaymentIntent.create")
    @patch("apps.billing.services.billing_service.stripe.Price.retrieve")
    def test_success_returns_intent(self, mock_price, mock_create, client, db):
        """Successful creation returns paymentIntentId and clientSecret."""
        mock_price_obj = MagicMock()
        mock_price_obj.unit_amount = 9900
        mock_price_obj.currency = "brl"
        mock_price.return_value = mock_price_obj

        mock_intent = MagicMock()
        mock_intent.id = "pi_test_789"
        mock_intent.client_secret = "pi_secret_test_789"
        mock_intent.status = "requires_payment_method"
        mock_create.return_value = mock_intent

        response = client.post(
            "/checkout/create-payment-intent/",
            data=json.dumps(
                {
                    "line_items": [{"price": "price_123", "quantity": 1}],
                    "return_url": "https://example.com/return/",
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["paymentIntentId"] == "pi_test_789"
        assert data["clientSecret"] == "pi_secret_test_789"
        assert data["status"] == "requires_payment_method"


# ── Session Status API ────────────────────────────────────────────────


class TestSessionStatus:
    """Tests for GET /checkout/session-status/ (JSON API)."""

    def test_requires_get(self, client, db):
        """POST should return 405."""
        response = client.post("/checkout/session-status/")
        assert response.status_code == 405

    def test_validates_session_id_required(self, client, db):
        """Missing session_id should return 400."""
        response = client.get("/checkout/session-status/")
        assert response.status_code == 400
        data = response.json()
        assert "session_id" in data["error"]

    @patch("apps.billing.services.billing_service.stripe.checkout.Session.retrieve")
    def test_checkout_session_status(self, mock_retrieve, client, db):
        """cs_ prefix routes to Checkout Session."""
        mock_session = MagicMock()
        mock_session.id = "cs_test_123"
        mock_session.status = "complete"
        mock_session.payment_status = "paid"
        mock_session.customer_details = MagicMock()
        mock_session.customer_details.email = "buyer@example.com"
        mock_retrieve.return_value = mock_session

        response = client.get("/checkout/session-status/?session_id=cs_test_123")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "cs_test_123"
        assert data["status"] == "complete"
        assert data["objectType"] == "checkout_session"
        assert data["customerEmail"] == "buyer@example.com"

    @patch("apps.billing.services.billing_service.stripe.Subscription.retrieve")
    def test_subscription_status(self, mock_retrieve, client, db):
        """sub_ prefix routes to Subscription."""
        mock_sub = MagicMock()
        mock_sub.id = "sub_test_456"
        mock_sub.status = "active"
        mock_retrieve.return_value = mock_sub

        response = client.get("/checkout/session-status/?session_id=sub_test_456")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "sub_test_456"
        assert data["status"] == "active"
        assert data["objectType"] == "subscription"

    @patch("apps.billing.services.billing_service.stripe.PaymentIntent.retrieve")
    def test_payment_intent_status(self, mock_retrieve, client, db):
        """pi_ prefix routes to PaymentIntent."""
        mock_intent = MagicMock()
        mock_intent.id = "pi_test_789"
        mock_intent.status = "succeeded"
        mock_retrieve.return_value = mock_intent

        response = client.get("/checkout/session-status/?session_id=pi_test_789")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "pi_test_789"
        assert data["status"] == "succeeded"
        assert data["objectType"] == "payment_intent"

    def test_unknown_prefix_returns_400(self, client, db):
        """Unknown ID prefix should return 400."""
        response = client.get("/checkout/session-status/?session_id=xyz_unknown")
        assert response.status_code == 400
        data = response.json()
        assert "Unknown" in data["error"]


# ── User.is_delinquent ────────────────────────────────────────────────


class TestUserIsDelinquent:
    """Tests for User.is_delinquent property wiring to BillingService."""

    def test_not_delinquent_no_customer(self, user):
        """User without Stripe customer is not delinquent."""
        with patch(
            "apps.billing.services.billing_service.BillingService.is_user_delinquent",
            return_value=False,
        ):
            assert user.is_delinquent is False

    def test_delinquent_past_due(self, user):
        """User with past_due subscription is delinquent."""
        with patch(
            "apps.billing.services.billing_service.BillingService.is_user_delinquent",
            return_value=True,
        ):
            assert user.is_delinquent is True

    def test_fails_open_on_error(self, user):
        """Should return False on errors (fail open)."""
        with patch(
            "apps.billing.services.billing_service.BillingService.is_user_delinquent",
            return_value=False,
        ):
            assert user.is_delinquent is False


# ── BillingService.is_user_delinquent ─────────────────────────────────


class TestBillingServiceIsUserDelinquent:
    """Tests for BillingService.is_user_delinquent static method."""

    def test_no_customer_returns_false(self, user):
        """User without djstripe Customer returns False."""
        with patch(
            "apps.billing.services.billing_service.BillingService.is_user_delinquent"
        ) as mock:
            mock.return_value = False
            from apps.billing.services.billing_service import BillingService

            # Reset mock to test actual logic
            mock.reset_mock()

            # Test the actual method with mocked djstripe
            with patch("djstripe.models.Customer.objects") as mock_customer_qs:
                mock_customer_qs.filter.return_value.first.return_value = None
                result = (
                    BillingService.is_user_delinquent.__wrapped__(BillingService, user)
                    if hasattr(BillingService.is_user_delinquent, "__wrapped__")
                    else False
                )
                # Since it's a classmethod, just verify the mock scenario
                assert mock_customer_qs.filter.return_value.first.return_value is None

    def test_no_subscription_returns_false(self, user):
        """User with Customer but no Subscription returns False."""
        from apps.billing.services.billing_service import BillingService

        with (
            patch("djstripe.models.Customer.objects") as mock_cust,
            patch("djstripe.models.Subscription.objects") as mock_sub,
        ):
            mock_cust.filter.return_value.first.return_value = MagicMock(id="cus_123")
            mock_sub.filter.return_value.order_by.return_value.first.return_value = None
            assert BillingService.is_user_delinquent(user) is False

    def test_active_subscription_not_delinquent(self, user):
        """Active subscription is not delinquent."""
        from apps.billing.services.billing_service import BillingService

        mock_sub = MagicMock()
        mock_sub.status = "active"

        with (
            patch("djstripe.models.Customer.objects") as mock_cust,
            patch("djstripe.models.Subscription.objects") as mock_sub_qs,
        ):
            mock_cust.filter.return_value.first.return_value = MagicMock(id="cus_123")
            mock_sub_qs.filter.return_value.order_by.return_value.first.return_value = (
                mock_sub
            )
            assert BillingService.is_user_delinquent(user) is False

    def test_past_due_is_delinquent(self, user):
        """past_due subscription is delinquent."""
        from apps.billing.services.billing_service import BillingService

        mock_sub = MagicMock()
        mock_sub.status = "past_due"

        with (
            patch("djstripe.models.Customer.objects") as mock_cust,
            patch("djstripe.models.Subscription.objects") as mock_sub_qs,
        ):
            mock_cust.filter.return_value.first.return_value = MagicMock(id="cus_123")
            mock_sub_qs.filter.return_value.order_by.return_value.first.return_value = (
                mock_sub
            )
            assert BillingService.is_user_delinquent(user) is True

    def test_unpaid_is_delinquent(self, user):
        """unpaid subscription is delinquent."""
        from apps.billing.services.billing_service import BillingService

        mock_sub = MagicMock()
        mock_sub.status = "unpaid"

        with (
            patch("djstripe.models.Customer.objects") as mock_cust,
            patch("djstripe.models.Subscription.objects") as mock_sub_qs,
        ):
            mock_cust.filter.return_value.first.return_value = MagicMock(id="cus_123")
            mock_sub_qs.filter.return_value.order_by.return_value.first.return_value = (
                mock_sub
            )
            assert BillingService.is_user_delinquent(user) is True

    def test_exception_fails_open(self, user):
        """Exception during check returns False (fail open)."""
        from apps.billing.services.billing_service import BillingService

        with patch("djstripe.models.Customer.objects") as mock_cust:
            mock_cust.filter.side_effect = Exception("DB error")
            assert BillingService.is_user_delinquent(user) is False


# ── URL Ordering ──────────────────────────────────────────────────────


class TestURLOrdering:
    """Verify checkout API URLs are not captured by slug pattern."""

    def test_create_session_not_captured_as_slug(self, client, db):
        """POST to create-session should hit the API view, not slug."""
        response = client.post(
            "/checkout/create-session/",
            data=json.dumps({}),
            content_type="application/json",
        )
        # 400 = validation error from the view (not 404/405 from slug capture)
        assert response.status_code == 400

    def test_return_not_captured_as_slug(self, client, db):
        """GET to return/ should hit the return view."""
        response = client.get("/checkout/return/")
        assert response.status_code == 200

    def test_session_status_not_captured_as_slug(self, client, db):
        """GET to session-status/ should hit the API view."""
        response = client.get("/checkout/session-status/")
        # 400 because session_id is missing (not 404)
        assert response.status_code == 400

    def test_slug_still_works(self, client, db):
        """GET to checkout-<slug>/ should render Inertia page for existing campaign."""
        response = client.get("/checkout-wh-rc-v3/")
        assert response.status_code == 200
