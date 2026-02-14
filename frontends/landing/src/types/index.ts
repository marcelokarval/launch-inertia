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
