import { useEffect, useRef } from 'react';
import { useForm } from '@inertiajs/react';

import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import PhoneInput from '@/components/PhoneInput';
import FingerprintProvider from '@/components/FingerprintProvider';
import { useFingerprint } from '@/hooks/use-fingerprint';
import { useCaptureIntent } from '@/hooks/use-capture-intent';
import type { CampaignFormConfig, PrefillData } from '@/types';

interface CaptureFormProps {
  campaignSlug: string;
  formConfig: CampaignFormConfig;
  fingerprintApiKey: string;
  /** Custom FingerprintJS endpoint (proxy subdomain) */
  fingerprintEndpoint?: string;
  /** Server-generated UUID linking events of the same page load session */
  captureToken: string;
  /** CapturePage public_id when available from the backend */
  capturePagePublicId?: string;
  /** Pre-fill data from session identity or capture-intent hints */
  prefill?: PrefillData;
  serverErrors?: Record<string, string>;
}

/**
 * Lead capture form — email + phone with hidden UTM/fingerprint fields.
 *
 * Uses Inertia useForm().post() for submission.
 * Server-side validation — errors come back as page props.
 *
 * FingerprintJS Pro SDK resolves visitor_id + request_id in parallel.
 * Cookie `fpjs_vid` is set by FingerprintProvider so Django middleware
 * can identify the visitor on subsequent requests.
 *
 * Pre-fill: returning visitors get email/phone from session identity
 * or from capture-intent hints (partial form data saved on blur).
 */
export default function CaptureForm({
  campaignSlug,
  formConfig,
  fingerprintApiKey,
  fingerprintEndpoint,
  captureToken,
  capturePagePublicId,
  prefill,
  serverErrors,
}: CaptureFormProps) {
  const hasSetUtm = useRef(false);
  const { visitorId, requestId, handleFingerprintResult } = useFingerprint();
  const { handleEmailBlur, handlePhoneBlur } = useCaptureIntent({
    captureToken,
    visitorId,
    requestId,
  });

  const { data, setData, post, processing, errors } = useForm({
    email: prefill?.email ?? '',
    phone: prefill?.phone ?? '',
    visitor_id: '',
    request_id: '',
    capture_token: captureToken,
    capture_page_public_id: capturePagePublicId ?? '',
    utm_source: '',
    utm_medium: '',
    utm_campaign: '',
    utm_content: '',
    utm_term: '',
    utm_id: '',
    // Ad tracking params (Meta CAPI, Voluum)
    fbclid: '',
    vk_ad_id: '',
    vk_source: '',
  });

  // Sync fingerprint data into form when it resolves
  useEffect(() => {
    if (visitorId && data.visitor_id !== visitorId) {
      setData((prev) => ({
        ...prev,
        visitor_id: visitorId,
        request_id: requestId,
      }));
    }
  }, [visitorId, requestId, data.visitor_id, setData]);

  // Populate UTM + ad tracking parameters from URL on mount
  useEffect(() => {
    if (hasSetUtm.current) return;
    hasSetUtm.current = true;

    const params = new URLSearchParams(window.location.search);

    // Standard UTM fields
    const utmFields = [
      'utm_source',
      'utm_medium',
      'utm_campaign',
      'utm_content',
      'utm_term',
      'utm_id',
    ] as const;

    // Ad tracking fields (fbclid for Meta CAPI, vk_ad_id, vk_source from Voluum)
    const adFields = ['fbclid', 'vk_ad_id', 'vk_source'] as const;

    const allValues: Record<string, string> = {};

    for (const field of utmFields) {
      const value = params.get(field);
      if (value) {
        allValues[field] = value;
      }
    }

    for (const field of adFields) {
      const value = params.get(field);
      if (value) {
        allValues[field] = value;
      }
    }

    if (Object.keys(allValues).length > 0) {
      setData((prev) => ({ ...prev, ...allValues }));
    }
  }, [setData]);

  // Merge server errors with Inertia client errors
  const allErrors = { ...serverErrors, ...errors };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    post(`/inscrever-${campaignSlug}/`, {
      forceFormData: true,
    });
  };

  return (
    <FingerprintProvider
      apiKey={fingerprintApiKey}
      endpoint={fingerprintEndpoint}
      onResult={handleFingerprintResult}
      captureToken={captureToken}
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Seu melhor e-mail"
          type="email"
          placeholder="nome@email.com"
          value={data.email}
          onChange={(e) => setData('email', e.target.value)}
          onBlur={(e) => handleEmailBlur(e.target.value)}
          error={allErrors.email}
          required
          autoComplete="email"
        />

        <PhoneInput
          label="Seu WhatsApp"
          value={data.phone}
          onChange={(phone) => setData('phone', phone)}
          onBlur={() => handlePhoneBlur(data.phone)}
          error={allErrors.phone}
          disabled={processing}
        />

        <Button
          type="submit"
          size="lg"
          isLoading={processing}
          loadingText={formConfig.loading_text}
          className={`w-full uppercase tracking-wide ${formConfig.button_gradient || formConfig.button_color} ${formConfig.button_hover_gradient || ''}`}
        >
          {formConfig.button_text}
        </Button>
      </form>
    </FingerprintProvider>
  );
}
