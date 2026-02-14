import '@testing-library/jest-dom/vitest'

// Mock i18next for all tests
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    i18n: {
      language: 'pt',
      changeLanguage: vi.fn(),
    },
  }),
  Trans: ({ children }: { children: React.ReactNode }) => children,
  initReactI18next: {
    type: '3rdParty',
    init: vi.fn(),
  },
}))

// Mock @inertiajs/react
vi.mock('@inertiajs/react', () => {
  const { createElement } = require('react')
  return {
    useForm: vi.fn(() => ({
      data: {},
      setData: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      patch: vi.fn(),
      delete: vi.fn(),
      processing: false,
      errors: {},
      reset: vi.fn(),
      clearErrors: vi.fn(),
      transform: vi.fn(),
      wasSuccessful: false,
      recentlySuccessful: false,
    })),
    usePage: vi.fn(() => ({
      props: {
        auth: { user: null },
        flash: {},
        locale: { language: 'pt' },
      },
    })),
    Link: ({ children, ...props }: any) =>
      createElement('a', props, children),
    router: {
      visit: vi.fn(),
      reload: vi.fn(),
      replace: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      patch: vi.fn(),
      delete: vi.fn(),
    },
  }
})
