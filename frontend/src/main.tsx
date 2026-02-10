import { createInertiaApp } from '@inertiajs/react'
import { createElement } from 'react'
import { createRoot } from 'react-dom/client'

// i18n must be imported before App to initialize translations
import './lib/i18n'

import './styles/globals.css'

createInertiaApp({
  title: (title) => `${title} - Launch`,
  resolve: async (name) => {
    const pages = import.meta.glob('./pages/**/*.tsx')
    const importPage = pages[`./pages/${name}.tsx`]
    if (!importPage) {
      throw new Error(`Page not found: ${name}`)
    }
    const module = await importPage()
    return module as Record<string, unknown>
  },
  setup({ el, App, props }) {
    const root = createRoot(el)
    root.render(createElement(App, props))
  },
  progress: {
    color: '#6366f1',
    showSpinner: true,
  },
})
