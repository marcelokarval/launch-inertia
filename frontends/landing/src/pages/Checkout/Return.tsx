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
 * Post-payment return page — dark theme.
 *
 * Stripe redirects here after embedded checkout completes.
 * Session status fetched from Django and displayed.
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
      <div className="mx-auto mb-4 h-12 w-12 animate-spin rounded-full border-4 border-gray-700 border-t-red-500" />
      <p className="text-gray-400">Verificando seu pagamento...</p>
    </div>
  );
}

function SuccessState({ email }: { email?: string }) {
  return (
    <div className="text-center">
      <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-green-900/30">
        <IconCheck className="h-8 w-8 text-green-400" />
      </div>
      <h2 className="mb-2 text-2xl font-bold text-white">
        Pagamento confirmado!
      </h2>
      <p className="mb-6 text-gray-400">
        Obrigado pela sua compra.
        {email && (
          <> Um e-mail de confirmação foi enviado para <strong className="text-white">{email}</strong>.</>
        )}
      </p>
      <Link
        href="/"
        className="inline-block rounded-lg bg-gradient-to-r from-[#0e036b] to-[#fb061a] px-6 py-3 text-sm font-semibold text-white transition-opacity hover:opacity-90"
      >
        Voltar ao início
      </Link>
    </div>
  );
}

function ProcessingState() {
  return (
    <div className="text-center">
      <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-yellow-900/30">
        <IconClock className="h-8 w-8 text-yellow-400" />
      </div>
      <h2 className="mb-2 text-2xl font-bold text-white">
        Pagamento em processamento
      </h2>
      <p className="text-gray-400">
        Seu pagamento está sendo processado. Você receberá um e-mail de confirmação em breve.
      </p>
    </div>
  );
}

function FailedState() {
  return (
    <div className="text-center">
      <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-red-900/30">
        <IconX className="h-8 w-8 text-red-400" />
      </div>
      <h2 className="mb-2 text-2xl font-bold text-white">
        Pagamento não concluído
      </h2>
      <p className="mb-6 text-gray-400">
        Houve um problema com seu pagamento. Por favor, tente novamente ou entre em contato com nosso suporte.
      </p>
      <Link
        href="/"
        className="inline-block rounded-lg bg-gradient-to-r from-[#0e036b] to-[#fb061a] px-6 py-3 text-sm font-semibold text-white transition-opacity hover:opacity-90"
      >
        Voltar ao início
      </Link>
    </div>
  );
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="text-center">
      <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-gray-800">
        <IconWarning className="h-8 w-8 text-gray-400" />
      </div>
      <h2 className="mb-2 text-2xl font-bold text-white">
        Algo deu errado
      </h2>
      <p className="mb-6 text-gray-400">{message}</p>
      <Link
        href="/"
        className="inline-block rounded-lg bg-gradient-to-r from-[#0e036b] to-[#fb061a] px-6 py-3 text-sm font-semibold text-white transition-opacity hover:opacity-90"
      >
        Voltar ao início
      </Link>
    </div>
  );
}
