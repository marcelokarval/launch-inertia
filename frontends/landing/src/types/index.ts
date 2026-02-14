/**
 * Landing frontend types.
 *
 * These types represent data passed from Django landing views as Inertia props.
 * Keep in sync with backend view return values.
 */

/** Shared props injected by InertiaShareMiddleware (if any apply to landing) */
export interface SharedProps {
  flash?: {
    success?: string;
    error?: string;
    warning?: string;
    info?: string;
  };
  errors?: Record<string, string>;
}

/** Props for the Home/Index placeholder page */
export interface HomeProps extends SharedProps {
  title: string;
  description: string;
}

/** Headline part — styled text segment */
export interface HeadlinePart {
  text: string;
  type: 'normal' | 'highlight';
}

/** Campaign badge (icon + text) */
export interface CampaignBadge {
  icon: string;
  text: string;
  visible: boolean;
}

/** Campaign form configuration */
export interface CampaignFormConfig {
  button_text: string;
  button_color: string;
  loading_text: string;
  thank_you_url: string;
}

/** Campaign trust badge */
export interface CampaignTrustBadge {
  enabled: boolean;
  text: string;
  icon: string;
}

/** Campaign social proof */
export interface CampaignSocialProof {
  enabled: boolean;
  value?: string;
  label?: string;
}

/** Campaign meta (SEO) */
export interface CampaignMeta {
  title: string;
  description: string;
}

/** Campaign headline */
export interface CampaignHeadline {
  parts: HeadlinePart[];
}

/** Full campaign props passed to the Capture page */
export interface CampaignProps {
  slug: string;
  meta: CampaignMeta;
  headline: CampaignHeadline;
  badges: CampaignBadge[];
  form: CampaignFormConfig;
  trust_badge: CampaignTrustBadge;
  social_proof: CampaignSocialProof;
}

/** Props for the Capture/Index page */
export interface CapturePageProps extends SharedProps {
  campaign: CampaignProps;
  fingerprint_api_key: string;
}

/** Props for the ThankYou/Index page */
export interface ThankYouPageProps extends SharedProps {
  campaign: {
    slug: string;
    meta: CampaignMeta;
  };
}

// ── Checkout Types ────────────────────────────────────────────────────

/** Line item configuration for Stripe checkout */
export interface CheckoutLineItem {
  price: string;
  quantity: number;
}

/** Checkout configuration from campaign JSON */
export interface CheckoutConfig {
  mode: 'subscription' | 'payment' | 'setup';
  line_items: CheckoutLineItem[];
  trial_period_days: number;
  phone_number_collection: boolean;
  billing_address_collection: 'auto' | 'required';
}

/** Props for the Checkout/Index page */
export interface CheckoutPageProps extends SharedProps {
  campaign_slug: string;
  stripe_publishable_key: string;
  checkout_config: CheckoutConfig;
  campaign_meta: CampaignMeta;
}

/** Props for the Checkout/Return page */
export interface CheckoutReturnProps extends SharedProps {
  session_id: string;
  stripe_publishable_key: string;
}

/** Response from POST /checkout/create-session/ */
export interface CreateSessionResponse {
  clientSecret: string;
  sessionId: string;
}

/** Response from POST /checkout/create-customer/ */
export interface CreateCustomerResponse {
  customerId: string;
  email: string;
  phone: string | null;
  name: string | null;
}

/** Response from POST /checkout/create-subscription/ */
export interface CreateSubscriptionResponse {
  subscriptionId: string;
  clientSecret: string;
  secretType: 'payment' | 'setup';
  status: string;
}

/** Response from POST /checkout/create-payment-intent/ */
export interface CreatePaymentIntentResponse {
  paymentIntentId: string;
  clientSecret: string;
  status: string;
}

/** Response from GET /checkout/session-status/ */
export interface SessionStatusResponse {
  id: string;
  status: string;
  objectType: 'checkout_session' | 'subscription' | 'payment_intent';
  customerEmail: string;
  extra: Record<string, unknown>;
}

/** Error response from checkout API endpoints */
export interface CheckoutErrorResponse {
  error: string;
}
