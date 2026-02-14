import { useCallback, useEffect, useRef } from 'react';
import { useForm } from '@inertiajs/react';

import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import PhoneInput from '@/components/PhoneInput';
import FingerprintProvider from '@/components/FingerprintProvider';
import type { CampaignFormConfig } from '@/types';

interface CaptureFormProps {
  campaignSlug: string;
  formConfig: CampaignFormConfig;
  fingerprintApiKey: string;
  serverErrors?: Record<string, string>;
}

/**
 * Lead capture form — email + phone with hidden UTM/fingerprint fields.
 *
 * Uses Inertia useForm().post() for submission.
 * Server-side validation — errors come back as page props.
 */
export default function CaptureForm({
  campaignSlug,
  formConfig,
  fingerprintApiKey,
  serverErrors,
}: CaptureFormProps) {
  const hasSetUtm = useRef(false);

  const { data, setData, post, processing, errors } = useForm({
    email: '',
    phone: '',
    visitor_id: '',
    request_id: '',
    utm_source: '',
    utm_medium: '',
    utm_campaign: '',
    utm_content: '',
    utm_term: '',
    utm_id: '',
  });

  // Populate UTM parameters from URL on mount
  useEffect(() => {
    if (hasSetUtm.current) return;
    hasSetUtm.current = true;

    const params = new URLSearchParams(window.location.search);
    const utmFields = [
      'utm_source',
      'utm_medium',
      'utm_campaign',
      'utm_content',
      'utm_term',
      'utm_id',
    ] as const;

    const utmValues: Record<string, string> = {};
    for (const field of utmFields) {
      const value = params.get(field);
      if (value) {
        utmValues[field] = value;
      }
    }

    if (Object.keys(utmValues).length > 0) {
      setData((prev) => ({ ...prev, ...utmValues }));
    }
  }, [setData]);

  // Merge server errors with Inertia client errors
  const allErrors = { ...serverErrors, ...errors };

  const handleFingerprintResult = useCallback(
    (visitorId: string, requestId: string) => {
      setData((prev) => ({
        ...prev,
        visitor_id: visitorId,
        request_id: requestId,
      }));
    },
    [setData],
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    post(`/inscrever-${campaignSlug}/`, {
      forceFormData: true,
    });
  };

  return (
    <>
      <FingerprintProvider
        apiKey={fingerprintApiKey}
        onResult={handleFingerprintResult}
      />

      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Seu melhor e-mail"
          type="email"
          placeholder="nome@email.com"
          value={data.email}
          onChange={(e) => setData('email', e.target.value)}
          error={allErrors.email}
          required
          autoComplete="email"
        />

        <PhoneInput
          label="Seu WhatsApp"
          value={data.phone}
          onChange={(phone) => setData('phone', phone)}
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
    </>
  );
}
