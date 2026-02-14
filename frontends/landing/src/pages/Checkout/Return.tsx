import { Link } from '@inertiajs/react';
import { useEffect, useState } from 'react';

import { IconCheck, IconClock, IconWarning, IconX } from '@/components/ui/icons';
import CheckoutLayout from '@/layouts/CheckoutLayout';
import { csrfFetch } from '@/lib/csrf';
import type {
  CheckoutReturnProps,
  SessionStatusResponse,
} from '@/types';

type PageState = 'loading' | 'success' | 'processing' | 'failed' | 'error';

/**
 * Post-payment return page.
 *
 * Stripe redirects here after embedded checkout completes.
 * The session_id is passed as a prop (from Django view, which reads the query param).
 * We fetch the session status from Django and display the result.
 */
export default function CheckoutReturn({
  session_id,
}: CheckoutReturnProps) {
  const [state, setState] = useState<PageState>('loading');
  const [sessionData, setSessionData] = useState<SessionStatusResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    if (!session_id) {
      setState('error');
      setErrorMessage('No session ID provided.');
      return;
    }

    const fetchStatus = async () => {
      try {
        const response = await csrfFetch(
          `/checkout/session-status/?session_id=${encodeURIComponent(session_id)}`,
          { method: 'GET' },
        );

        if (!response.ok) {
          const errorData = await response.json();
          setState('error');
          setErrorMessage(errorData.error || 'Failed to retrieve payment status.');
          return;
        }

        const data = (await response.json()) as SessionStatusResponse;
        setSessionData(data);

        // Map Stripe status to page state
        if (data.status === 'complete' || data.status === 'active' || data.status === 'succeeded') {
          setState('success');
        } else if (data.status === 'processing' || data.status === 'trialing' || data.status === 'incomplete') {
          setState('processing');
        } else {
          setState('failed');
        }
      } catch {
        setState('error');
        setErrorMessage('Unable to check payment status. Please try again.');
      }
    };

    fetchStatus();
  }, [session_id]);

  return (
    <CheckoutLayout>
      <div className="mx-auto max-w-lg py-12">
        {state === 'loading' && <LoadingState />}
        {state === 'success' && <SuccessState email={sessionData?.customerEmail} />}
        {state === 'processing' && <ProcessingState />}
        {state === 'failed' && <FailedState />}
        {state === 'error' && <ErrorState message={errorMessage} />}
      </div>
    </CheckoutLayout>
  );
}

function LoadingState() {
  return (
    <div className="text-center">
      <div className="mx-auto mb-4 h-12 w-12 animate-spin rounded-full border-4 border-gray-200 border-t-indigo-600" />
      <p className="text-gray-600">Verificando seu pagamento...</p>
    </div>
  );
}

function SuccessState({ email }: { email?: string }) {
  return (
    <div className="text-center">
      <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
        <IconCheck className="h-8 w-8 text-green-600" />
      </div>
      <h2 className="mb-2 text-2xl font-bold text-gray-900">
        Pagamento confirmado!
      </h2>
      <p className="mb-6 text-gray-600">
        Obrigado pela sua compra.
        {email && (
          <> Um e-mail de confirmação foi enviado para <strong>{email}</strong>.</>
        )}
      </p>
      <Link
        href="/"
        className="inline-block rounded-lg bg-indigo-600 px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-indigo-700"
      >
        Voltar ao início
      </Link>
    </div>
  );
}

function ProcessingState() {
  return (
    <div className="text-center">
      <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-yellow-100">
        <IconClock className="h-8 w-8 text-yellow-600" />
      </div>
      <h2 className="mb-2 text-2xl font-bold text-gray-900">
        Pagamento em processamento
      </h2>
      <p className="text-gray-600">
        Seu pagamento está sendo processado. Você receberá um e-mail de confirmação em breve.
      </p>
    </div>
  );
}

function FailedState() {
  return (
    <div className="text-center">
      <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-red-100">
        <IconX className="h-8 w-8 text-red-600" />
      </div>
      <h2 className="mb-2 text-2xl font-bold text-gray-900">
        Pagamento não concluído
      </h2>
      <p className="mb-6 text-gray-600">
        Houve um problema com seu pagamento. Por favor, tente novamente ou entre em contato com nosso suporte.
      </p>
      <Link
        href="/"
        className="inline-block rounded-lg bg-indigo-600 px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-indigo-700"
      >
        Voltar ao início
      </Link>
    </div>
  );
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="text-center">
      <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-gray-100">
        <IconWarning className="h-8 w-8 text-gray-500" />
      </div>
      <h2 className="mb-2 text-2xl font-bold text-gray-900">
        Algo deu errado
      </h2>
      <p className="mb-6 text-gray-600">{message}</p>
      <Link
        href="/"
        className="inline-block rounded-lg bg-indigo-600 px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-indigo-700"
      >
        Voltar ao início
      </Link>
    </div>
  );
}
