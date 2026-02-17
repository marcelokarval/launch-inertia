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
  type: 'normal' | 'highlight' | 'underline';
  /** Color hint for highlights: 'red' = bg-red pill, 'white' = plain white */
  color?: 'red' | 'white' | 'yellow' | 'green' | 'blue';
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
  /** Optional gradient for CTA button (e.g., 'bg-gradient-to-r from-[#0e036b] to-[#fb061a]') */
  button_gradient?: string;
  /** Hover gradient for CTA button */
  button_hover_gradient?: string;
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
  /** Optional subheadline below the main headline */
  subheadline?: string;
  badges: CampaignBadge[];
  form: CampaignFormConfig;
  trust_badge: CampaignTrustBadge;
  social_proof: CampaignSocialProof;
  /** Background image URL for the capture layout */
  background_image?: string;
  /** Highlight color override (default: #FB061A) */
  highlight_color?: string;
}

/** Props for the Capture/Index page */
export interface CapturePageProps extends SharedProps {
  campaign: CampaignProps;
  fingerprint_api_key: string;
  /** Server-generated UUID linking events of the same page load session */
  capture_token: string;
}

/** Thank-you page step indicator */
export interface ThankYouStep {
  label: string;
  completed: boolean;
}

/** Thank-you page configuration (from campaign JSON) */
export interface ThankYouConfig {
  headline: string;
  subheadline: string;
  whatsapp_group_link: string;
  whatsapp_button_text: string;
  countdown_minutes: number;
  show_social_proof: boolean;
  social_proof_text: string;
  steps: ThankYouStep[];
  progress_percentage: number;
}

/** Props for the ThankYou/Index page */
export interface ThankYouPageProps extends SharedProps {
  campaign: {
    slug: string;
    meta: CampaignMeta;
  };
  thank_you: ThankYouConfig;
}

// ── Support Types ─────────────────────────────────────────────────────

/** FAQ item (question + answer with category) */
export interface FAQItem {
  id: string;
  category: string;
  question: string;
  answer: string;
}

/** Chatwoot configuration passed from Django */
export interface ChatwootConfig {
  website_token: string;
  base_url: string;
  locale: string;
  header_title: string;
  header_subtitle: string;
  business_hours: string;
}

/** Support page configuration */
export interface SupportConfig {
  chatwoot: ChatwootConfig;
  faq_items: FAQItem[];
  faq_categories: string[];
}

/** Props for the Support/Index page */
export interface SupportPageProps extends SharedProps {
  support: SupportConfig;
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
