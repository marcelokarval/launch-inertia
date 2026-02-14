/**
 * Global TypeScript types for the application.
 *
 * These types match the backend `to_dict()` serialization output.
 * All pages should import from here instead of defining local interfaces.
 *
 * Naming convention:
 * - `id` always maps to backend `public_id` (the URL-safe identifier)
 * - Field names match the backend JSON keys exactly
 */

// ============================================================================
// User & Auth Types (matching identity.models.User.to_dict())
// ============================================================================

/**
 * Shared user object as returned by InertiaShareMiddleware.
 * This is the lightweight version available on every page via `usePage()`.
 */
export interface SharedUser {
  id: string
  email: string
  name: string
  avatar?: string | null
  is_staff: boolean
  is_superuser: boolean
}

/**
 * Full user object as returned by User.to_dict() in identity views.
 */
export interface User {
  id: string
  email: string
  name: string
  first_name: string
  last_name: string
  status: UserStatus
  setup_status: SetupStatusValue
  email_verified: boolean
  mfa_enabled: boolean
  timezone: string
  language: string
  is_staff: boolean
  is_delinquent: boolean
  date_joined: string | null
}

export type UserStatus = 'active' | 'inactive' | 'pending' | 'suspended' | 'locked'
export type SetupStatusValue = 'incomplete' | 'basic' | 'complete'

/**
 * Profile as returned by Profile.to_dict().
 */
export interface UserProfile {
  id: string
  phone: string
  bio: string
  avatar_url: string | null
  address: {
    line1: string
    line2: string
    city: string
    state: string
    postal_code: string
    country: string
  }
  notification_preferences: Record<string, unknown>
  agreed_to_terms: boolean
  terms_accepted_at: string | null
  terms_version: string
  can_access_system: boolean
}

// ============================================================================
// Identity Types (matching contact_identity.models.Identity)
// ============================================================================

export interface Tag {
  id: string
  name: string
  color: string
}

/** Identity as shown in list views (Index page). */
export interface IdentityListItem {
  id: string
  display_name: string
  status: IdentityStatus
  confidence_score: number
  primary_email: string | null
  primary_phone: string | null
  email_count: number
  phone_count: number
  fingerprint_count: number
  tags: Tag[]
  lifecycle_global: Record<string, unknown>
  last_seen: string | null
  created_at: string | null
}

// ============================================================================
// Identity Resolution Types (matching contact_identity.models)
// ============================================================================

export type IdentityStatus = 'active' | 'merged' | 'inactive'

/** Identity as returned by Identity.to_dict(include_contacts=True). */
export interface IdentityDetail {
  id: string
  status: IdentityStatus
  merged_into_id: string | null
  last_seen: string | null
  first_seen_source: string | null
  confidence_score: number
  email_count: number
  phone_count: number
  fingerprint_count: number
  emails: ChannelEmail[]
  phones: ChannelPhone[]
  fingerprints: DeviceFingerprint[]
  created_at: string
}

/** Attribution as returned by Attribution.to_dict(). */
export interface Attribution {
  id: string
  identity_id: string
  utm_source: string
  utm_medium: string
  utm_campaign: string
  utm_content: string
  utm_term: string
  referrer: string
  landing_page: string
  touchpoint_type: string
  created_at: string
}

// ============================================================================
// Contact Channel Types (matching contact_email/contact_phone models)
// ============================================================================

export type EmailLifecycleStatus =
  | 'pending'
  | 'active'
  | 'invalid'
  | 'bounced_soft'
  | 'bounced_hard'
  | 'complained'
  | 'unsubscribed'

/** ContactEmail as returned by ContactEmail.to_dict(). */
export interface ChannelEmail {
  id: string
  value: string
  original_value: string
  domain: string
  lifecycle_status: EmailLifecycleStatus
  is_verified: boolean
  verified_at: string | null
  is_dnc: boolean
  is_deliverable: boolean
  quality_score: number
  first_seen: string | null
  last_seen: string | null
  identity_id: string | null
}

export type PhoneType = 'mobile' | 'landline' | 'voip' | 'unknown'

/** ContactPhone as returned by ContactPhone.to_dict(). */
export interface ChannelPhone {
  id: string
  value: string
  original_value: string
  country_code: string
  phone_type: PhoneType
  display_value: string
  is_verified: boolean
  verified_at: string | null
  is_whatsapp: boolean
  is_sms_capable: boolean
  is_dnc: boolean
  first_seen: string | null
  last_seen: string | null
  identity_id: string | null
}

// ============================================================================
// Fingerprint / Device Types (matching contact_fingerprint models)
// ============================================================================

export interface FraudSignal {
  type: string
  severity: 'low' | 'medium' | 'high'
  description: string
}

/** FingerprintIdentity as returned by FingerprintIdentity.to_dict(). */
export interface DeviceFingerprint {
  id: string
  hash: string
  confidence_score: number
  device_type: string
  visitor_found: boolean
  device_info: Record<string, unknown>
  browser_info: Record<string, unknown>
  geo_info: Record<string, unknown>
  browser: string
  browser_family: string
  os: string
  ip_address: string | null
  first_seen: string | null
  last_seen: string | null
  is_master: boolean
  is_mobile: boolean
  identity_id: string | null
  fraud_signals: FraudSignal[]
}

/** FingerprintEvent as returned by FingerprintEvent.to_dict(). */
export interface TimelineEvent {
  id: string
  event_type: string
  page_url: string | null
  timestamp: string
  user_data: Record<string, unknown>
  event_data: Record<string, unknown>
  session_id: string | null
  fingerprint_id: string
}

// ============================================================================
// Identity Detail Extended (for Show page with full identity data)
// ============================================================================

/** Full identity detail with channels, attributions, timeline for Show page. */
export interface IdentityShowData extends IdentityDetail {
  display_name: string
  operator_notes: string
  tags: Tag[]
  lifecycle_global: Record<string, unknown>
  attributions: Attribution[]
  timeline: TimelineEvent[]
}

/** Chip color helpers for identity/channel status. */
export const EMAIL_LIFECYCLE_CHIP_COLOR: Record<EmailLifecycleStatus, 'accent' | 'success' | 'warning' | 'danger' | 'default'> = {
  pending: 'accent',
  active: 'success',
  invalid: 'danger',
  bounced_soft: 'warning',
  bounced_hard: 'danger',
  complained: 'danger',
  unsubscribed: 'default',
}

export const IDENTITY_STATUS_CHIP_COLOR: Record<IdentityStatus, 'success' | 'warning' | 'default'> = {
  active: 'success',
  merged: 'warning',
  inactive: 'default',
}

// ============================================================================
// Notification Types (matching notifications.models.Notification.to_dict())
// ============================================================================

export type NotificationType = 'info' | 'success' | 'warning' | 'error' | 'action'

export interface Notification {
  id: string
  type: NotificationType
  title: string
  body: string
  action_url: string
  action_label: string
  is_read: boolean
  read_at: string | null
  created_at: string
  actor: SharedUser | null
}

// ============================================================================
// Stripe & Billing Types (using djstripe / BillingService output)
// ============================================================================

export type SubscriptionStatus =
  | 'active'
  | 'past_due'
  | 'unpaid'
  | 'canceled'
  | 'incomplete'
  | 'incomplete_expired'
  | 'trialing'
  | 'paused'

export interface Subscription {
  id: string
  status: SubscriptionStatus
  plan_name?: string
  current_period_start?: string
  current_period_end?: string
  cancel_at_period_end?: boolean
}

export interface Invoice {
  id: string
  status: 'draft' | 'open' | 'paid' | 'uncollectible' | 'void'
  amount_due: number
  amount_paid?: number
  currency?: string
  created: string
  hosted_invoice_url?: string
  invoice_pdf?: string
}

export interface Plan {
  id: string
  name: string
  description?: string
  amount: number
  currency: string
  interval: 'day' | 'week' | 'month' | 'year'
  interval_count: number
  /** Formatted price for display (0 = free). Used by onboarding PlanSelection. */
  price?: number
  /** Feature list for display in plan cards. */
  features?: string[]
}

export interface PaymentMethod {
  id: string
  type: string
  card?: {
    brand: string
    last4: string
    exp_month: number
    exp_year: number
  }
}

// ============================================================================
// Form Data Types
// ============================================================================

export interface LoginFormData {
  username: string  // Backend expects 'username' field (email value)
  password: string
  remember_me?: boolean
}

export interface RegisterFormData {
  email: string
  password: string
  first_name?: string
  last_name?: string
}

export interface VerifyEmailFormData {
  verification_code: string
}

export interface LegalAgreementsFormData {
  agreed_to_terms: boolean
  agreed_to_privacy: boolean
  agreed_to_marketing?: boolean
}

export interface ProfileCompletionFormData {
  first_name: string
  last_name: string
  phone: string
  state: string
  timezone: string
  company_name?: string
  experience_level?: string
  hear_about_us?: string
}

/** Form data for creating/importing an identity. */
export interface IdentityFormData {
  email?: string
  phone?: string
  display_name?: string
}

/** Form data for editing identity operator fields. */
export interface IdentityEditFormData {
  display_name: string
  operator_notes: string
  tag_ids: string[]
}

export interface PasswordChangeFormData {
  old_password: string
  new_password: string
  new_password_confirmation: string
}

export interface PasswordResetFormData {
  email: string
}

export interface PasswordResetConfirmFormData {
  verification_code: string
  new_password: string
}

// ============================================================================
// Setup & Onboarding Types
// ============================================================================

export interface SetupStatus {
  current_stage: string
  completed_stages: string[]
  progress_percentage: number
  is_complete: boolean
  required_actions: string[]
}

// ============================================================================
// Shared Component Prop Types
// ============================================================================

export interface BaseComponentProps {
  className?: string
  children?: React.ReactNode
}

export interface FormFieldProps extends BaseComponentProps {
  label?: string
  error?: string
  required?: boolean
  disabled?: boolean
}

// ============================================================================
// Pagination (matching backend service output)
// ============================================================================

export interface Pagination {
  page: number
  per_page: number
  total: number
  pages: number
}

// ============================================================================
// Dashboard & Analytics Types
// ============================================================================

export interface DashboardStats {
  total_identities: number
  active_subscriptions: number
  unread_notifications: number
  conversion_rate: number
}

// ============================================================================
// Status Color Helpers
// ============================================================================

export const NOTIFICATION_TYPE_COLORS: Record<NotificationType, { bg: string; text: string }> = {
  info: { bg: 'bg-primary-100', text: 'text-primary-600' },
  success: { bg: 'bg-success-100', text: 'text-success-600' },
  warning: { bg: 'bg-warning-100', text: 'text-warning-600' },
  error: { bg: 'bg-danger-100', text: 'text-danger-600' },
  action: { bg: 'bg-secondary-100', text: 'text-secondary-600' },
}
