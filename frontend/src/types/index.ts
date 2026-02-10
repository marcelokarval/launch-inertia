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
// Contact & CRM Types (matching contacts.models.Contact.to_dict())
// ============================================================================

export type ContactStatus = 'lead' | 'prospect' | 'customer' | 'churned' | 'inactive'

export type ContactSource = 'manual' | 'import' | 'form' | 'api' | 'integration'

export interface Tag {
  id: string
  name: string
  color: string
}

/**
 * Contact as returned by Contact.to_dict() (list view).
 */
export interface Contact {
  id: string
  name: string
  email: string
  phone: string
  company: string
  job_title: string
  status: ContactStatus
  lead_score: number
  source: ContactSource
  email_verified: boolean
  phone_verified: boolean
  created_at: string
  tags: Tag[]
}

/**
 * Contact with details as returned by Contact.to_dict(include_details=True).
 */
export interface ContactDetail extends Contact {
  notes: string
  custom_fields: Record<string, unknown>
  owner: SharedUser | null
  created_by: SharedUser | null
  metadata: Record<string, unknown>
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

export interface ContactFormData {
  name: string
  email?: string
  phone?: string
  company?: string
  job_title?: string
  notes?: string
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
  total_contacts: number
  active_subscriptions: number
  unread_notifications: number
  conversion_rate: number
}

// ============================================================================
// Status Color Helpers
// ============================================================================

/** HeroUI Chip color mapping for contact statuses */
export const CONTACT_STATUS_CHIP_COLOR: Record<ContactStatus, 'accent' | 'warning' | 'success' | 'danger' | 'default'> = {
  lead: 'accent',
  prospect: 'warning',
  customer: 'success',
  churned: 'danger',
  inactive: 'default',
}

/** @deprecated Use CONTACT_STATUS_CHIP_COLOR with HeroUI Chip color prop instead */
export const CONTACT_STATUS_COLORS: Record<ContactStatus, { bg: string; text: string }> = {
  lead: { bg: 'bg-primary-100', text: 'text-primary-800' },
  prospect: { bg: 'bg-warning-100', text: 'text-warning-800' },
  customer: { bg: 'bg-success-100', text: 'text-success-800' },
  churned: { bg: 'bg-danger-100', text: 'text-danger-800' },
  inactive: { bg: 'bg-default-100', text: 'text-default-800' },
}

export const NOTIFICATION_TYPE_COLORS: Record<NotificationType, { bg: string; text: string }> = {
  info: { bg: 'bg-primary-100', text: 'text-primary-600' },
  success: { bg: 'bg-success-100', text: 'text-success-600' },
  warning: { bg: 'bg-warning-100', text: 'text-warning-600' },
  error: { bg: 'bg-danger-100', text: 'text-danger-600' },
  action: { bg: 'bg-secondary-100', text: 'text-secondary-600' },
}
