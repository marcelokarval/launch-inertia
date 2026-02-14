import { useCallback, useMemo, useState } from 'react';
import { loadStripe } from '@stripe/stripe-js';
import {
  EmbeddedCheckout,
  EmbeddedCheckoutProvider,
} from '@stripe/react-stripe-js';

import CheckoutLayout from '@/layouts/CheckoutLayout';
import { csrfFetch } from '@/lib/csrf';
import type {
  CheckoutPageProps,
  CreateSessionResponse,
  CheckoutErrorResponse,
} from '@/types';

/**
 * Embedded Stripe Checkout page.
 *
 * Receives campaign checkout config from Django props, then:
 * 1. Loads Stripe.js with the publishable key (memoized)
 * 2. Creates a Checkout Session via Django JSON endpoint
 * 3. Mounts the <EmbeddedCheckout> component with the client secret
 *
 * The return_url uses Stripe's {CHECKOUT_SESSION_ID} template variable
 * which Stripe replaces with the actual session ID on redirect.
 */
export default function CheckoutIndex({
  stripe_publishable_key,
  checkout_config,
  campaign_meta,
}: CheckoutPageProps) {
  const [error, setError] = useState<string | null>(null);

  // Memoize to avoid calling loadStripe on every render
  const stripePromise = useMemo(
    () => loadStripe(stripe_publishable_key),
    [stripe_publishable_key],
  );

  const fetchClientSecret = useCallback(async (): Promise<string> => {
    const returnUrl = `${window.location.origin}/checkout/return/?session_id={CHECKOUT_SESSION_ID}`;

    const response = await csrfFetch('/checkout/create-session/', {
      method: 'POST',
      body: JSON.stringify({
        line_items: checkout_config.line_items,
        mode: checkout_config.mode,
        return_url: returnUrl,
        trial_period_days: checkout_config.trial_period_days,
        phone_number_collection: checkout_config.phone_number_collection,
        billing_address_collection: checkout_config.billing_address_collection,
      }),
    });

    if (!response.ok) {
      const errorData = (await response.json()) as CheckoutErrorResponse;
      const message = errorData.error || 'Failed to create checkout session';
      setError(message);
      throw new Error(message);
    }

    const data = (await response.json()) as CreateSessionResponse;
    return data.clientSecret;
  }, [checkout_config]);

  if (!checkout_config.line_items.length) {
    return (
      <CheckoutLayout title={campaign_meta?.title}>
        <div className="rounded-lg border border-yellow-600/50 bg-yellow-900/20 p-6 text-center">
          <p className="text-yellow-400">
            Configuração de checkout não disponível para esta campanha.
          </p>
        </div>
      </CheckoutLayout>
    );
  }

  return (
    <CheckoutLayout title={campaign_meta?.title}>
      {error && (
        <div className="mb-6 rounded-lg border border-red-600/50 bg-red-900/20 p-4 text-center">
          <p className="text-sm text-red-400">{error}</p>
        </div>
      )}
      <div id="checkout">
        <EmbeddedCheckoutProvider
          stripe={stripePromise}
          options={{ fetchClientSecret }}
        >
          <EmbeddedCheckout />
        </EmbeddedCheckoutProvider>
      </div>
    </CheckoutLayout>
  );
}
