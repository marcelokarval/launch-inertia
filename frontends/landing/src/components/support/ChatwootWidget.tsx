import { useEffect, useRef, useState, useCallback } from 'react';

import { IconAlertCircle, IconMessageCircle, IconSpinner } from '@/components/ui/icons';
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
 * Chatwoot SDK widget — EMBEDDED approach.
 *
 * Unlike a simple toggle('open'), this component physically moves the
 * Chatwoot .woot-widget-holder DOM node INTO our container div, making
 * the chat appear inline within the page layout (not as a floating popup).
 *
 * Ported from legacy embedded-chat-widget.tsx.
 */
export default function ChatwootWidget({
  config,
  className = '',
  autoOpen = true,
}: ChatwootWidgetProps) {
  const [widgetState, setWidgetState] = useState<WidgetState>('loading');
  const [errorMessage, setErrorMessage] = useState('');
  const containerRef = useRef<HTMLDivElement>(null);
  const scriptLoadedRef = useRef(false);
  const embeddedRef = useRef(false);
  const reopenAttemptsRef = useRef(0);

  /** Move the Chatwoot widget holder into our container */
  const embedWidget = useCallback(() => {
    if (embeddedRef.current || !containerRef.current) return;

    const holder = document.querySelector('.woot-widget-holder') as HTMLElement;
    if (!holder) return;

    embeddedRef.current = true;

    // Move into our container
    containerRef.current.appendChild(holder);

    // Force styles for inline embedding
    holder.style.position = 'absolute';
    holder.style.inset = '0';
    holder.style.width = '100%';
    holder.style.height = '100%';
    holder.style.zIndex = '1';
    holder.style.boxShadow = 'none';
    holder.style.borderRadius = '0';

    // Style iframe inside
    const iframe = holder.querySelector('iframe') as HTMLIFrameElement;
    if (iframe) {
      iframe.style.width = '100%';
      iframe.style.height = '100%';
      iframe.style.border = 'none';
      iframe.style.borderRadius = '0 0 16px 16px';
    }
  }, []);

  const handleReady = useCallback(() => {
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
        // Give Chatwoot time to render, then embed
        setTimeout(embedWidget, 300);
      }, 100);
    }
  }, [autoOpen, embedWidget]);

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
      setErrorMessage('Não foi possível carregar o chat');
    };

    document.head.appendChild(script);

    // Slow connection timeout
    const timeout = setTimeout(() => {
      setWidgetState((prev) => {
        if (prev === 'loading') {
          setErrorMessage('Conexão lenta. O chat pode demorar para carregar.');
          return 'offline';
        }
        return prev;
      });
    }, 10000);

    // Poll for widget holder (backup for embed)
    const pollInterval = setInterval(() => {
      if (!embeddedRef.current) {
        embedWidget();
      } else {
        clearInterval(pollInterval);
      }
    }, 500);

    return () => {
      clearTimeout(timeout);
      clearInterval(pollInterval);
      window.removeEventListener('chatwoot:ready', handleReady);
      window.removeEventListener('chatwoot:error', handleError);
    };
  }, [config, handleReady, handleError, embedWidget]);

  const handleRetry = useCallback(() => {
    setWidgetState('loading');
    setErrorMessage('');
    embeddedRef.current = false;
    reopenAttemptsRef.current = 0;

    if (window.chatwootSDK) {
      window.chatwootSDK.run({
        websiteToken: config.website_token,
        baseUrl: config.base_url,
      });
    } else {
      window.location.reload();
    }
  }, [config]);

  const handleReopen = useCallback(() => {
    reopenAttemptsRef.current = 0;
    window.$chatwoot?.toggle('open');
    setTimeout(embedWidget, 300);
  }, [embedWidget]);

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
        <p className={`text-xs ${statusColor.replace('bg-', 'text-').replace(' animate-pulse', '')}`}>
          {statusText}
        </p>
      </div>
    </div>
  );

  const baseClasses = `flex flex-col rounded-2xl border border-zinc-800 bg-zinc-900 overflow-hidden ${className}`;

  // Loading
  if (widgetState === 'loading') {
    return (
      <div className={baseClasses}>
        {header('bg-yellow-500 animate-pulse', 'Conectando...')}
        <div className="flex flex-1 items-center justify-center">
          <div className="flex flex-col items-center gap-3 text-white">
            <IconSpinner className="h-8 w-8 text-red-500" />
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
            <IconAlertCircle className="h-12 w-12 text-red-500" />
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
        {header('bg-yellow-500 animate-pulse', 'Carregando...')}
        <div className="flex flex-1 items-center justify-center p-6">
          <div className="flex flex-col items-center gap-4 text-center">
            <IconSpinner className="h-10 w-10 text-yellow-500" />
            <div>
              <p className="mb-1 font-medium text-white">Conexão lenta</p>
              <p className="text-sm text-gray-400">{errorMessage}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Ready — container for embedded Chatwoot
  return (
    <div className={baseClasses}>
      {header('bg-green-500', config.header_subtitle)}

      {/* Embedded Chatwoot container */}
      <div
        id="chatwoot-embed-container"
        ref={containerRef}
        className="relative flex-1 bg-zinc-950"
      >
        {/* Fallback if widget not yet embedded */}
        {!embeddedRef.current && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="flex flex-col items-center gap-3">
              <IconSpinner className="h-6 w-6 text-red-500" />
              <span className="text-sm text-gray-500">Carregando conversa...</span>
            </div>
          </div>
        )}
      </div>

      {/* Reopen button (shown if chat gets minimized) */}
      <div className="flex items-center justify-between border-t border-zinc-800 bg-zinc-800/30 px-4 py-2">
        <span className="text-xs text-gray-500">Chat ao vivo</span>
        <button
          onClick={handleReopen}
          className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs text-gray-400 transition-colors hover:bg-zinc-700 hover:text-white"
        >
          <IconMessageCircle className="h-3.5 w-3.5" />
          Reabrir chat
        </button>
      </div>
    </div>
  );
}
