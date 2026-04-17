import { FormEvent, useMemo, useState } from 'react';
import { loadStripe } from '@stripe/stripe-js';
import {
  Elements,
  PaymentElement,
  useElements,
  useStripe,
} from '@stripe/react-stripe-js';

import CheckoutLayout from '@/layouts/CheckoutLayout';
import { csrfFetch } from '@/lib/csrf';
import type {
  CheckoutErrorResponse,
  CheckoutPageProps,
  CreateCustomerResponse,
  CreatePaymentIntentResponse,
  CreateSubscriptionResponse,
} from '@/types';

/**
 * Public checkout page using Stripe Elements.
 *
 * Flow:
 * 1. Collect buyer identity information
 * 2. Create customer + subscription OR payment intent via Django server actions
 * 3. Mount Stripe Elements with the returned client secret
 * 4. Confirm payment/setup and redirect to /checkout/return/
 */
export default function CheckoutIndex({
  stripe_publishable_key,
  checkout_config,
  campaign_meta,
  campaign_slug,
}: CheckoutPageProps) {
  const [error, setError] = useState<string | null>(null);
  const [isInitializing, setIsInitializing] = useState(false);
  const [checkoutState, setCheckoutState] = useState<{
    clientSecret: string;
    objectId: string;
    secretType: 'payment' | 'setup';
  } | null>(null);
  const [customer, setCustomer] = useState({
    email: '',
    name: '',
    phone: '',
  });

  const stripePromise = useMemo(
    () => loadStripe(stripe_publishable_key),
    [stripe_publishable_key],
  );

  const startCheckout = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    setIsInitializing(true);

    try {
      if (!customer.email.trim()) {
        throw new Error('Informe seu e-mail para continuar.');
      }

      if (checkout_config.mode === 'subscription' || checkout_config.mode === 'setup') {
        const customerResponse = await csrfFetch('/checkout/create-customer/', {
          method: 'POST',
          body: JSON.stringify({
            email: customer.email.trim().toLowerCase(),
            name: customer.name.trim() || undefined,
            phone: customer.phone.trim() || undefined,
            metadata: { campaign_slug },
          }),
        });

        if (!customerResponse.ok) {
          const errorData = (await customerResponse.json()) as CheckoutErrorResponse;
          throw new Error(errorData.error || 'Falha ao criar cliente Stripe.');
        }

        const customerData = (await customerResponse.json()) as CreateCustomerResponse;

        const subscriptionResponse = await csrfFetch('/checkout/create-subscription/', {
          method: 'POST',
          body: JSON.stringify({
            customer_id: customerData.customerId,
            line_items: checkout_config.line_items,
            trial_period_days: checkout_config.trial_period_days,
            metadata: {
              campaign_slug,
              customer_email: customerData.email,
            },
          }),
        });

        if (!subscriptionResponse.ok) {
          const errorData = (await subscriptionResponse.json()) as CheckoutErrorResponse;
          throw new Error(errorData.error || 'Falha ao criar assinatura.');
        }

        const subscriptionData = (await subscriptionResponse.json()) as CreateSubscriptionResponse;
        setCheckoutState({
          clientSecret: subscriptionData.clientSecret,
          objectId: subscriptionData.subscriptionId,
          secretType: subscriptionData.secretType,
        });
      } else {
        const paymentIntentResponse = await csrfFetch('/checkout/create-payment-intent/', {
          method: 'POST',
          body: JSON.stringify({
            line_items: checkout_config.line_items,
            return_url: `${window.location.origin}/checkout/return/`,
            customer_email: customer.email.trim().toLowerCase(),
            metadata: {
              campaign_slug,
              customer_name: customer.name.trim() || '',
            },
          }),
        });

        if (!paymentIntentResponse.ok) {
          const errorData = (await paymentIntentResponse.json()) as CheckoutErrorResponse;
          throw new Error(errorData.error || 'Falha ao criar PaymentIntent.');
        }

        const paymentIntentData = (await paymentIntentResponse.json()) as CreatePaymentIntentResponse;
        setCheckoutState({
          clientSecret: paymentIntentData.clientSecret,
          objectId: paymentIntentData.paymentIntentId,
          secretType: 'payment',
        });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao iniciar checkout.');
    } finally {
      setIsInitializing(false);
    }
  };

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

      {!checkoutState ? (
        <form
          onSubmit={startCheckout}
          className="mx-auto max-w-xl space-y-4 rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-sm"
        >
          <div>
            <h2 className="text-2xl font-semibold text-white">Finalizar compra</h2>
            <p className="mt-2 text-sm text-white/70">
              Preencha seus dados para iniciar o pagamento com Stripe Elements.
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <label className="space-y-2 md:col-span-2">
              <span className="text-sm font-medium text-white">E-mail</span>
              <input
                type="email"
                required
                value={customer.email}
                onChange={(e) => setCustomer((prev) => ({ ...prev, email: e.target.value }))}
                className="w-full rounded-lg border border-white/15 bg-black/30 px-4 py-3 text-white outline-none placeholder:text-white/35"
                placeholder="voce@exemplo.com"
              />
            </label>
            <label className="space-y-2">
              <span className="text-sm font-medium text-white">Nome</span>
              <input
                type="text"
                value={customer.name}
                onChange={(e) => setCustomer((prev) => ({ ...prev, name: e.target.value }))}
                className="w-full rounded-lg border border-white/15 bg-black/30 px-4 py-3 text-white outline-none placeholder:text-white/35"
                placeholder="Seu nome"
              />
            </label>
            <label className="space-y-2">
              <span className="text-sm font-medium text-white">Telefone</span>
              <input
                type="tel"
                value={customer.phone}
                onChange={(e) => setCustomer((prev) => ({ ...prev, phone: e.target.value }))}
                className="w-full rounded-lg border border-white/15 bg-black/30 px-4 py-3 text-white outline-none placeholder:text-white/35"
                placeholder="(11) 99999-9999"
              />
            </label>
          </div>

          <button
            type="submit"
            disabled={isInitializing}
            className="w-full rounded-lg bg-gradient-to-r from-[#0e036b] to-[#fb061a] px-6 py-3 text-sm font-semibold text-white transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isInitializing ? 'Preparando checkout...' : 'Continuar para pagamento'}
          </button>
        </form>
      ) : (
        <Elements
          stripe={stripePromise}
          options={{
            clientSecret: checkoutState.clientSecret,
            appearance: {
              theme: 'night',
              variables: {
                colorPrimary: '#fb061a',
                colorBackground: '#111111',
                colorText: '#ffffff',
              },
            },
          }}
        >
          <ElementsCheckoutForm
            objectId={checkoutState.objectId}
            secretType={checkoutState.secretType}
          />
        </Elements>
      )}
    </CheckoutLayout>
  );
}

function ElementsCheckoutForm({
  objectId,
  secretType,
}: {
  objectId: string;
  secretType: 'payment' | 'setup';
}) {
  const stripe = useStripe();
  const elements = useElements();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!stripe || !elements) {
      return;
    }

    setError(null);
    setIsSubmitting(true);

    const submitResult = await elements.submit();
    if (submitResult.error) {
      setError(
        submitResult.error.message ||
          'Não foi possível validar o formulário de pagamento.',
      );
      setIsSubmitting(false);
      return;
    }

    const returnUrl = `${window.location.origin}/checkout/return/?session_id=${encodeURIComponent(objectId)}`;

    const result =
      secretType === 'setup'
        ? await stripe.confirmSetup({
            elements,
            confirmParams: { return_url: returnUrl },
          })
        : await stripe.confirmPayment({
            elements,
            confirmParams: { return_url: returnUrl },
          });

    if (result.error) {
      setError(result.error.message || 'Falha ao confirmar pagamento.');
      setIsSubmitting(false);
      return;
    }

    setIsSubmitting(false);
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="mx-auto max-w-xl space-y-6 rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-sm"
    >
      {error && (
        <div className="rounded-lg border border-red-600/50 bg-red-900/20 p-4 text-sm text-red-300">
          {error}
        </div>
      )}

      <PaymentElement />

      <button
        type="submit"
        disabled={!stripe || !elements || isSubmitting}
        className="w-full rounded-lg bg-gradient-to-r from-[#0e036b] to-[#fb061a] px-6 py-3 text-sm font-semibold text-white transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {isSubmitting ? 'Confirmando...' : 'Confirmar pagamento'}
      </button>
    </form>
  );
}
