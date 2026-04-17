/**
 * Landing frontend types.
 *
 * These types represent data passed from Django landing views as Inertia props.
 * Keep in sync with backend view return values.
 */

/** Shared props injected by InertiaShareMiddleware for all landing pages */
export interface SharedProps {
  flash?: {
    success?: string;
    error?: string;
    warning?: string;
    info?: string;
  };
  fingerprint?: {
    api_key: string;
    endpoint: string;
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

/** Pre-fill data for returning visitors */
export interface PrefillData {
  email?: string;
  phone?: string;
}

/** Props for the Capture/Index page */
export interface CapturePageProps extends SharedProps {
  campaign: CampaignProps;
  /** Server-generated UUID linking events of the same page load session */
  capture_token: string;
  /** CapturePage public_id when this landing is already backed by the DB */
  capture_page_public_id?: string;
  /** Pre-fill data from session identity or capture-intent hints */
  prefill?: PrefillData;
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

// ── FingerprintJS Pro Types ──────────────────────────────────────────

/** FingerprintJS Pro result stored on window for global access */
export interface FingerprintResult {
  visitorId: string;
  requestId: string;
  confidence: { score: number };
  visitorFound: boolean;
  /** Timestamp when the SDK loaded */
  loadedAt: number;
  /** Time in ms the SDK took to load and resolve */
  loadTime: number;
}

/** FingerprintJS configuration passed from Django as Inertia props */
export interface FingerprintConfig {
  apiKey: string;
  endpoint?: string;
}

// ── AgreliFlix Types (CPL video lesson series) ──────────────────────

/** Chapter marker within an episode */
export interface AgrelliflixChapter {
  title: string;
  start_seconds: number;
}

/** Episode — server-parsed with availability flags from Django view */
export interface AgrelliflixEpisode {
  id: number;
  video_id: string;
  title: string;
  subtitle: string;
  description: string;
  duration: string;
  /** ISO 8601 string with timezone (parsed server-side from Miami TZ) */
  live_date: string;
  /** ISO 8601 — when episode becomes available */
  available_at: string;
  /** ISO 8601 — when episode expires */
  expires_at: string;
  /** Server-computed: true if live hasn't happened yet */
  is_live_pending: boolean;
  /** Server-computed: true if episode is currently available */
  is_available: boolean;
  /** Server-computed: true if episode has expired */
  is_expired: boolean;
  available_days_from_now: number;
  expires_days_from_now: number;
  youtube_url: string | null;
  chapters: AgrelliflixChapter[];
}

/** Video progress for a single episode (stored in localStorage) */
export interface VideoProgress {
  episodeId: number;
  watchedSeconds: number;
  totalSeconds: number;
  percentage: number;
  lastWatchedAt: string;
  completed: boolean;
}

/** Map of episode ID → progress */
export type ProgressRecord = Record<number, VideoProgress>;

/** Achievement definition from campaign config */
export interface AgrelliflixAchievement {
  id: string;
  title: string;
  description: string;
  icon: string;
  points: number;
}

/** Achievement IDs supported by the system */
export type AchievementId =
  | 'early_bird'
  | 'binge_watcher'
  | 'completionist'
  | 'speed_demon'
  | 'social_butterfly';

/** CTA configurations */
export interface AgrelliflixPreRollCTA {
  text: string;
  url_campaign: string;
  show_after_ms: number;
  skippable: boolean;
  skip_after_ms: number;
}

export interface AgrelliflixMidRollCTA {
  text: string;
  url_campaign: string;
  show_at_percent: number;
  duration_ms: number;
}

export interface AgrelliflixEndScreenCTA {
  text: string;
  url_campaign: string;
  show_before_end_seconds: number;
}

export interface AgrelliflixFloatingCTA {
  text: string;
  url_campaign: string;
  show_after_completion_percent: number;
}

export interface AgrelliflixCTAConfig {
  pre_roll: AgrelliflixPreRollCTA;
  mid_roll: AgrelliflixMidRollCTA;
  end_screen: AgrelliflixEndScreenCTA;
  floating: AgrelliflixFloatingCTA;
}

/** Social proof testimonial */
export interface AgrelliflixTestimonial {
  name: string;
  location: string;
  text: string;
}

/** Social proof stats strip */
export interface AgrelliflixStats {
  total_students: number;
  average_profit: number;
  success_rate: number;
  rating: number;
}

/** Social proof configuration */
export interface AgrelliflixSocialProofConfig {
  enabled: boolean;
  initial_viewers: number;
  variance_range: number;
  update_interval_ms: number;
  testimonials: AgrelliflixTestimonial[];
  stats: AgrelliflixStats;
}

/** Cart configuration with server-computed open status */
export interface AgrelliflixCartConfig {
  /** ISO 8601 — cart open date (parsed from Miami TZ) */
  open_date: string;
  pre_open_url: string;
  post_open_url: string;
  button_text: string;
  /** Server-computed: true if cart is currently open */
  is_open: boolean;
}

/** WhatsApp floating button config */
export interface AgrelliflixWhatsAppConfig {
  enabled: boolean;
  number: string;
  message: string;
}

/** Branding config */
export interface AgrelliflixBrandingConfig {
  series_title: string;
  badge_text: string;
}

/** Theme color tokens (Netflix-inspired dark theme) */
export interface AgrelliflixThemeConfig {
  black_deep: string;
  black_soft: string;
  grey_dark: string;
  grey_medium: string;
  grey_light: string;
  white_soft: string;
  red_primary: string;
  red_hover: string;
  gold_accent: string;
}

/** Banner URL config */
export interface AgrelliflixBannerUrls {
  aulas_1_2: string;
  aulas_3_4: string;
}

/** Tracking config */
export interface AgrelliflixTrackingConfig {
  page_name: string;
  event_subtype: string;
}

/** Full AgreliFlix config received as Inertia props (server-parsed) */
export interface AgrelliflixConfig {
  slug: string;
  meta: CampaignMeta;
  branding: AgrelliflixBrandingConfig;
  theme: AgrelliflixThemeConfig;
  episodes: AgrelliflixEpisode[];
  achievements: Record<AchievementId, AgrelliflixAchievement>;
  ctas: AgrelliflixCTAConfig;
  social_proof: AgrelliflixSocialProofConfig;
  cart: AgrelliflixCartConfig;
  whatsapp: AgrelliflixWhatsAppConfig;
  banner_urls: AgrelliflixBannerUrls;
  tracking: AgrelliflixTrackingConfig;
}

/** Props for the AgreliFlix/Index page */
export interface AgrelliflixPageProps extends SharedProps {
  config: AgrelliflixConfig;
  initial_episode_id: number;
  page_name: string;
}

// ── AgreliFlix Hook Return Types ────────────────────────────────────

export interface UseVideoProgressReturn {
  progress: ProgressRecord;
  saveProgress: (episodeId: number, watchedSeconds: number, totalSeconds: number) => boolean;
  getEpisodeProgress: (episodeId: number) => VideoProgress | null;
  getOverallProgress: () => number;
  hasWatchedAll: (totalEpisodes: number) => boolean;
  getNextEpisode: (episodes: AgrelliflixEpisode[]) => AgrelliflixEpisode | null;
  resetProgress: () => void;
}

export interface UseEpisodeUnlocksReturn {
  unlockedEpisodes: number[];
  checkUnlocks: () => void;
  isUnlocked: (episodeId: number) => boolean;
}

export interface UseAchievementsReturn {
  achievements: string[];
  unlockAchievement: (id: string) => void;
  hasAchievement: (id: string) => boolean;
}

export interface UseViewerSimulationReturn {
  currentViewers: number;
}

/** XP level definition for gamification */
export interface XPLevel {
  name: string;
  minXP: number;
  maxXP: number;
  color: string;
}

/** Gamification storage state (persisted in localStorage) */
export interface AgrelliflixStorageState {
  totalXP: number;
  level: string;
  achievements: string[];
  streak: number;
  lastVisit: string;
  episodesCompleted: number[];
  shareCount: number;
}

/* ===================================================================
 * Onboarding (Post-Purchase) Page
 * =================================================================== */

/** Onboarding page configuration */
export interface OnboardingConfig {
  /** YouTube video ID */
  video_id: string;
  /** Page title displayed above the video */
  title: string;
  /** Marquee header items */
  marquee_items: string[];
  /** Marquee header background color */
  marquee_color: string;
  /** Background image URL */
  background_image: string;
  /** WhatsApp group link (optional) */
  whatsapp_link?: string;
}

/** Props for Onboarding/Index page */
export interface OnboardingPageProps extends SharedProps {
  config: OnboardingConfig;
}

/* ===================================================================
 * Lembrete BF (Black Friday Reminder) Page
 * =================================================================== */

/** Course card in the BF reminder page */
export interface BFCourseCard {
  title: string;
  description: string;
  image: string;
}

/** Bonus tier in the BF page */
export interface BFBonus {
  tier: string;
  title: string;
  description: string;
}

/** Price comparison entry */
export interface BFPriceEntry {
  label: string;
  value: string;
}

/** Lembrete BF page configuration */
export interface LembreteBFConfig {
  /** Target date for countdown (ISO 8601) */
  target_date: string;
  /** CTA link (WhatsApp group or checkout) */
  cta_link: string;
  /** CTA button text */
  cta_text: string;
  /** Hero headline */
  headline: string;
  /** Hero benefits list */
  benefits: string[];
  /** Course cards */
  courses: BFCourseCard[];
  /** Bonus tiers */
  bonuses: BFBonus[];
  /** Normal price entries (strikethrough) */
  normal_prices: BFPriceEntry[];
  /** Special offer price */
  special_price: string;
  /** Special offer installments text */
  installments_text: string;
  /** Background images */
  images: {
    logo: string;
    hero_cross?: string;
    summary_bg?: string;
    phone_mockup?: string;
    warning_bg?: string;
  };
}

/** Props for LembreteBF/Index page */
export interface LembreteBFPageProps extends SharedProps {
  config: LembreteBFConfig;
}

/* ===================================================================
 * Suporte Launch (Video Background Support) Page
 * =================================================================== */

/** Suporte Launch page configuration */
export interface SuporteLaunchConfig {
  /** YouTube video ID for background */
  video_id: string;
  /** Header title */
  title: string;
  /** Header subtitle */
  subtitle: string;
  /** CTA link (inscription page) */
  cta_link: string;
  /** CTA button text */
  cta_text: string;
  /** Chatwoot config (same as support page) */
  chatwoot: {
    website_token: string;
    base_url: string;
    locale: string;
  };
}

/** Props for SuporteLaunch/Index page */
export interface SuporteLaunchPageProps extends SharedProps {
  config: SuporteLaunchConfig;
}

/* ===================================================================
 * Recado Importante (Long-Form Sales Page)
 * =================================================================== */

/** Video testimonial entry */
export interface VideoTestimonial {
  video_id: string;
  name: string;
  description: string;
}

/** Course module entry */
export interface CourseModule {
  title: string;
  description: string;
}

/** Bonus entry for the sales page */
export interface SalesBonus {
  title: string;
  description: string;
  value: string;
  image?: string;
}

/** Recado Importante page configuration */
export interface RecadoImportanteConfig {
  /** Hero video ID */
  video_id: string;
  /** CTA WhatsApp group link */
  cta_link: string;
  /** CTA button text */
  cta_text: string;
  /** Countdown target date (ISO 8601) */
  target_date?: string;
  /** Expert/instructor info */
  expert: {
    name: string;
    title: string;
    description: string;
    image?: string;
  };
  /** Video testimonials */
  testimonials: VideoTestimonial[];
  /** Course description text */
  course_description: string;
  /** Course modules list */
  modules: CourseModule[];
  /** Bonuses */
  bonuses: SalesBonus[];
  /** Mega bonus (featured) */
  mega_bonus?: SalesBonus;
  /** Pricing section */
  pricing: {
    original_price: string;
    current_price: string;
    installments_text: string;
    discount_text: string;
  };
  /** Background images */
  images: {
    hero_bg?: string;
    course_map?: string;
  };
}

/** Props for RecadoImportante/Index page */
export interface RecadoImportantePageProps extends SharedProps {
  config: RecadoImportanteConfig;
}
