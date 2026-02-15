import { useEffect, useRef } from 'react';

/**
 * ChatwootGlobalLoader — loads Chatwoot SDK globally for the landing frontend.
 *
 * This component loads the Chatwoot SDK script once and configures it with
 * hideMessageBubble=true so it doesn't show the default floating button.
 * The WhatsAppFloatingButton component (mode="chatwoot") can then call
 * window.$chatwoot.toggle('open') on any page.
 *
 * Must be rendered once at the app root level (main.tsx).
 * The Support page has its own ChatwootWidget that embeds the chat inline,
 * so this loader skips injection if already loaded.
 */

const CHATWOOT_BASE_URL = 'https://atend.arthuragrelli.com';
const CHATWOOT_WEBSITE_TOKEN = '7c97wiFhBxyidsXA6tXN5kJc';

export default function ChatwootGlobalLoader() {
  const loadedRef = useRef(false);

  useEffect(() => {
    // Don't load twice (Support page may load its own instance)
    if (loadedRef.current || window.chatwootSDK) return;
    loadedRef.current = true;

    // Configure Chatwoot to hide its own bubble (we use WhatsAppFloatingButton)
    window.chatwootSettings = {
      hideMessageBubble: true,
      position: 'right',
      locale: 'pt_BR',
      type: 'standard',
      darkMode: 'dark',
      launcherTitle: 'Suporte Arthur Agrelli',
    };

    const script = document.createElement('script');
    script.src = `${CHATWOOT_BASE_URL}/packs/js/sdk.js`;
    script.async = true;
    script.defer = true;

    script.onload = () => {
      if (window.chatwootSDK) {
        window.chatwootSDK.run({
          websiteToken: CHATWOOT_WEBSITE_TOKEN,
          baseUrl: CHATWOOT_BASE_URL,
        });
      }
    };

    document.head.appendChild(script);
  }, []);

  return null;
}
