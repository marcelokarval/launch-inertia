import { createInertiaApp } from '@inertiajs/react';
import { createElement } from 'react';
import type { ReactNode } from 'react';
import { createRoot } from 'react-dom/client';

import ChatwootGlobalLoader from '@/components/ChatwootGlobalLoader';
import GlobalFingerprintInit from '@/components/GlobalFingerprintInit';
import './styles/globals.css';

/**
 * App shell that wraps the Inertia <App> with global components.
 *
 * GlobalFingerprintInit uses `usePage()` and MUST be rendered inside
 * the Inertia component tree (<App> provides the page context).
 * ChatwootGlobalLoader doesn't need Inertia context but lives here
 * for consistency.
 */
function AppShell({ children }: { children: ReactNode }) {
  return createElement(
    'div',
    null,
    createElement(ChatwootGlobalLoader),
    createElement(GlobalFingerprintInit),
    children,
  );
}

createInertiaApp({
  title: (title) => `${title} - Arthur Agrelli`,
  resolve: async (name) => {
    const pages = import.meta.glob('./pages/**/*.tsx');
    const importPage = pages[`./pages/${name}.tsx`];
    if (!importPage) {
      throw new Error(`Page not found: ${name}`);
    }
    const module = await importPage();
    const page = module as { default: { layout?: unknown } };

    // Wrap every page with AppShell so global components have access
    // to usePage() (they're now inside the Inertia tree).
    // Compose existing layout WITH AppShell to ensure GlobalFingerprintInit
    // is always rendered, even for pages with custom layouts.
    const existingLayout = page.default.layout;
    page.default.layout = (pageContent: ReactNode) => {
      const content = existingLayout
        ? (existingLayout as (children: ReactNode) => ReactNode)(pageContent)
        : pageContent;
      return createElement(AppShell, null, content);
    };

    return page;
  },
  setup({ el, App, props }) {
    const root = createRoot(el);
    root.render(createElement(App, props));
  },
  progress: {
    color: '#E50914',
    showSpinner: true,
  },
});
