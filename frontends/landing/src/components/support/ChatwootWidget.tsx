import { useEffect, useRef, useState, useCallback } from 'react';

import type { ChatwootConfig } from '@/types';

/** Chatwoot SDK global types */
declare global {
  interface Window {
    chatwootSettings?: {
      hideMessageBubble: boolean;
      position: string;
      locale: string;
      type: string;
      darkMode: string;
      launcherTitle: string;
    };
    chatwootSDK?: {
      run: (config: { websiteToken: string; baseUrl: string }) => void;
    };
    $chatwoot?: {
      toggle: (state?: 'open' | 'close') => void;
      setUser: (id: string, data: Record<string, unknown>) => void;
      setCustomAttributes: (attrs: Record<string, unknown>) => void;
    };
  }
}

type WidgetState = 'loading' | 'ready' | 'error' | 'offline';

interface ChatwootWidgetProps {
  config: ChatwootConfig;
  className?: string;
  autoOpen?: boolean;
}

/**
 * Chatwoot SDK widget — standalone approach.
 *
 * Loads the Chatwoot SDK script, configures settings, and auto-opens
 * the chat widget on the support page. Shows loading/error/offline
 * states with retry capability.
 *
 * Configuration comes from Django props (not hardcoded).
 */
export default function ChatwootWidget({
  config,
  className = '',
  autoOpen = true,
}: ChatwootWidgetProps) {
  const [widgetState, setWidgetState] = useState<WidgetState>('loading');
  const [errorMessage, setErrorMessage] = useState('');
  const scriptLoadedRef = useRef(false);
  const readyHandledRef = useRef(false);

  const handleReady = useCallback(() => {
    if (readyHandledRef.current) return;
    readyHandledRef.current = true;
    setWidgetState('ready');

    if (window.$chatwoot) {
      window.$chatwoot.setCustomAttributes({
        page: '/suporte',
        source: 'suporte_embedded',
      });
    }

    if (autoOpen && window.$chatwoot) {
      setTimeout(() => {
        window.$chatwoot?.toggle('open');
      }, 100);
    }
  }, [autoOpen]);

  const handleError = useCallback(() => {
    setWidgetState('error');
    setErrorMessage('Erro ao conectar com o suporte');
  }, []);

  // Load SDK
  useEffect(() => {
    if (scriptLoadedRef.current) return;
    scriptLoadedRef.current = true;

    window.chatwootSettings = {
      hideMessageBubble: true,
      position: 'right',
      locale: config.locale,
      type: 'expanded_bubble',
      darkMode: 'dark',
      launcherTitle: config.header_title,
    };

    window.addEventListener('chatwoot:ready', handleReady);
    window.addEventListener('chatwoot:error', handleError);

    const script = document.createElement('script');
    script.src = `${config.base_url}/packs/js/sdk.js`;
    script.async = true;
    script.defer = true;

    script.onload = () => {
      if (window.chatwootSDK) {
        window.chatwootSDK.run({
          websiteToken: config.website_token,
          baseUrl: config.base_url,
        });
      }
    };

    script.onerror = () => {
      setWidgetState('error');
      setErrorMessage('Nao foi possivel carregar o chat');
    };

    document.head.appendChild(script);

    const timeout = setTimeout(() => {
      setWidgetState((prev) => {
        if (prev === 'loading') {
          setErrorMessage('Conexao lenta. O chat pode demorar para carregar.');
          return 'offline';
        }
        return prev;
      });
    }, 10000);

    return () => {
      clearTimeout(timeout);
      window.removeEventListener('chatwoot:ready', handleReady);
      window.removeEventListener('chatwoot:error', handleError);
    };
  }, [config, handleReady, handleError]);

  const handleRetry = useCallback(() => {
    setWidgetState('loading');
    setErrorMessage('');
    readyHandledRef.current = false;

    if (window.chatwootSDK) {
      window.chatwootSDK.run({
        websiteToken: config.website_token,
        baseUrl: config.base_url,
      });
    } else {
      window.location.reload();
    }
  }, [config]);

  const toggleChat = useCallback(() => {
    window.$chatwoot?.toggle();
  }, []);

  // Shared header
  const header = (statusColor: string, statusText: string) => (
    <div className="flex items-center gap-3 border-b border-zinc-700 bg-zinc-800/50 p-4">
      <div className="relative">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-red-500 to-red-700">
          <span className="text-sm font-bold text-white">AA</span>
        </div>
        <div
          className={`absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full border-2 border-zinc-800 ${statusColor}`}
        />
      </div>
      <div className="flex-1">
        <h3 className="font-semibold text-white">{config.header_title}</h3>
        <p className={`text-xs ${statusColor.replace('bg-', 'text-')}`}>{statusText}</p>
      </div>
    </div>
  );

  const baseClasses = `flex flex-col rounded-2xl border border-zinc-800 bg-zinc-900 ${className}`;

  // Loading
  if (widgetState === 'loading') {
    return (
      <div className={baseClasses}>
        {header('bg-yellow-500', 'Conectando...')}
        <div className="flex flex-1 items-center justify-center">
          <div className="flex flex-col items-center gap-3 text-white">
            {/* Spinner */}
            <svg className="h-8 w-8 animate-spin text-red-500" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <span className="text-gray-400">Carregando chat...</span>
          </div>
        </div>
      </div>
    );
  }

  // Error
  if (widgetState === 'error') {
    return (
      <div className={baseClasses}>
        {header('bg-red-500', 'Offline')}
        <div className="flex flex-1 items-center justify-center p-6">
          <div className="flex flex-col items-center gap-4 text-center">
            {/* Alert icon */}
            <svg className="h-12 w-12 text-red-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            <div>
              <p className="mb-1 font-medium text-white">Erro ao conectar</p>
              <p className="text-sm text-gray-400">{errorMessage}</p>
            </div>
            <button
              onClick={handleRetry}
              className="rounded-lg bg-red-600 px-6 py-2 text-sm text-white transition-colors hover:bg-red-700"
            >
              Tentar novamente
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Offline / slow
  if (widgetState === 'offline') {
    return (
      <div className={baseClasses}>
        {header('bg-yellow-500', 'Carregando...')}
        <div className="flex flex-1 items-center justify-center p-6">
          <div className="flex flex-col items-center gap-4 text-center">
            <svg className="h-10 w-10 animate-spin text-yellow-500" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <div>
              <p className="mb-1 font-medium text-white">Conexao lenta</p>
              <p className="text-sm text-gray-400">{errorMessage}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Ready
  return (
    <div className={baseClasses}>
      <div className="flex items-center gap-3 border-b border-zinc-700 bg-zinc-800/50 p-4">
        <div className="relative">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-red-500 to-red-700">
            <span className="text-sm font-bold text-white">AA</span>
          </div>
          <div className="absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full border-2 border-zinc-800 bg-green-500" />
        </div>
        <div className="flex-1">
          <h3 className="font-semibold text-white">{config.header_title}</h3>
          <p className="text-xs text-green-400">{config.header_subtitle}</p>
        </div>
        <button
          onClick={toggleChat}
          className="rounded-lg p-2 transition-colors hover:bg-zinc-700"
          title="Toggle chat"
        >
          {/* MessageCircle icon */}
          <svg className="h-5 w-5 text-gray-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
          </svg>
        </button>
      </div>

      <div className="relative flex-1">
        <div className="absolute inset-0 flex items-center justify-center text-sm text-gray-500">
          <span>Chat carregado - clique para interagir</span>
        </div>
      </div>
    </div>
  );
}
