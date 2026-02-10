/**
 * Login Page - HeroUI v3 Nativo + Inertia.js
 *
 * Design: Split-panel layout igual ao dashboard-react-para-launch
 * - Esquerda: Gradient com features e stats
 * - Direita: Formulário de login
 */

import { useState } from 'react'
import { Head, Link } from '@inertiajs/react'
import { useTranslation } from 'react-i18next'
import {
  Form,
  TextField,
  Input,
  Label,
  FieldError,
  Checkbox,
  Card,
  Chip,
} from '@heroui/react'
import { Button } from '@/components/ui'
import {
  Rocket,
  BarChart3,
  Zap,
  Users,
  Target,
  User,
  Lock,
  Eye,
  EyeOff,
  ArrowRight,
  AlertCircle,
  Sparkles,
} from 'lucide-react'
import { LanguageSelector, ThemeToggle } from '@/components/ui'
import { useAppForm } from '@/hooks/useAppForm'

interface Props {
  errors?: Record<string, string>
  needs_verification?: boolean
  verification_email?: string | null
}

export default function Login({ errors = {}, needs_verification = false, verification_email = null }: Props) {
  const { t } = useTranslation()
  const { t: tc } = useTranslation('components')
  const { t: tCommon } = useTranslation('common')

  const [showPassword, setShowPassword] = useState(false)

  const features = [
    {
      icon: Target,
      title: tc('authLayout.features.campaignManagement.title'),
      description: tc('authLayout.features.campaignManagement.description'),
    },
    {
      icon: BarChart3,
      title: tc('authLayout.features.analytics.title'),
      description: tc('authLayout.features.analytics.description'),
    },
    {
      icon: Users,
      title: tc('authLayout.features.leadManagement.title'),
      description: tc('authLayout.features.leadManagement.description'),
    },
    {
      icon: Zap,
      title: tc('authLayout.features.automations.title'),
      description: tc('authLayout.features.automations.description'),
    },
  ]

  const { data, setData, submit, isSubmitting } = useAppForm({
    initialData: {
      username: '',  // Django AuthenticationForm expects 'username' field
      password: '',
      remember_me: false as boolean,
    },
    url: '/auth/login/',
    method: 'post',
  })

  return (
    <>
      <Head title={t('auth.login.pageTitle')} />

      <div className="min-h-screen flex flex-col lg:flex-row">
        {/* Left Panel - Features (Desktop) / Bottom (Mobile) */}
        <div className="order-2 lg:order-1 lg:flex-1 bg-gradient-to-br from-indigo-600 via-purple-600 to-indigo-700 relative overflow-hidden flex">
          {/* Grid Pattern Overlay */}
          <div
            className="absolute inset-0 opacity-10"
            style={{
              backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.4'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
            }}
          />

          <div className="relative z-10 flex flex-col justify-center items-center lg:items-start px-8 lg:px-12 py-12 text-white w-full">
            <div className="space-y-8 max-w-lg w-full">
              {/* Logo and Title */}
              <div className="space-y-4 text-center lg:text-left">
                {/* Desktop Logo */}
                <div className="hidden lg:flex items-center space-x-3">
                  <div className="p-3 rounded-xl bg-white/10 backdrop-blur-sm">
                    <Rocket className="h-8 w-8" />
                  </div>
                  <div>
                    <h1 className="text-4xl font-bold">{tCommon('brand.name')}</h1>
                    <p className="text-lg opacity-90">{tCommon('brand.version')}</p>
                  </div>
                </div>

                {/* Mobile Logo */}
                <div className="lg:hidden flex flex-col items-center space-y-2">
                  <div className="p-3 rounded-xl bg-white/10 backdrop-blur-sm">
                    <Zap className="h-8 w-8" />
                  </div>
                  <div className="text-center">
                    <h2 className="text-2xl font-bold">{tc('authLayout.features.title')}</h2>
                    <p className="text-sm opacity-90">{tc('authLayout.features.subtitle')}</p>
                  </div>
                </div>

                <p className="text-lg lg:text-xl opacity-90 max-w-md mx-auto lg:mx-0">
                  {tc('authLayout.features.subtitle')}
                </p>
              </div>

              {/* Features Grid */}
              <div className="grid gap-6 w-full">
                {features.map((feature, index) => (
                  <div
                    key={index}
                    className="flex items-start space-x-4 animate-fade-in"
                    style={{ animationDelay: `${index * 100}ms` }}
                  >
                    <div className="p-2 rounded-lg bg-white/10 backdrop-blur-sm">
                      <feature.icon className="h-5 w-5" />
                    </div>
                    <div>
                      <h3 className="font-semibold">{feature.title}</h3>
                      <p className="text-sm opacity-80">{feature.description}</p>
                    </div>
                  </div>
                ))}
              </div>

              {/* Stats */}
              <div className="pt-8 border-t border-white/20">
                <div className="flex items-center justify-center lg:justify-start space-x-8">
                  <div className="text-center lg:text-left">
                    <p className="text-3xl font-bold">+127%</p>
                    <p className="text-sm opacity-80">{tc('authLayout.stats.avgRoi')}</p>
                  </div>
                  <div className="text-center lg:text-left">
                    <p className="text-3xl font-bold">2.4k</p>
                    <p className="text-sm opacity-80">{tc('authLayout.stats.launches')}</p>
                  </div>
                  <div className="text-center lg:text-left">
                    <p className="text-3xl font-bold">99.9%</p>
                    <p className="text-sm opacity-80">{tc('authLayout.stats.uptime')}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Decorative Blurred Circles */}
          <div className="absolute top-20 right-20 w-64 h-64 bg-white/5 rounded-full blur-3xl" />
          <div className="absolute bottom-20 left-20 w-96 h-96 bg-white/5 rounded-full blur-3xl" />
        </div>

        {/* Right Panel - Login Form */}
        <div className="order-1 lg:order-2 flex-1 flex items-center justify-center bg-background p-8 relative">
          {/* Header controls */}
          <div className="absolute top-4 right-4 flex items-center gap-1">
            <LanguageSelector visualOnly />
            <ThemeToggle />
          </div>

          <div className="w-full max-w-md space-y-8">
            {/* Mobile Logo */}
            <div className="lg:hidden text-center space-y-4">
              <div className="flex justify-center">
                <div className="p-3 rounded-xl bg-gradient-to-br from-indigo-600 to-purple-600">
                  <Rocket className="h-8 w-8 text-white" />
                </div>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-foreground">{tCommon('brand.name')}</h1>
                <p className="text-default-500">{tCommon('brand.version')}</p>
              </div>
            </div>

            {/* Login Card */}
            <Card className="w-full shadow-xl border border-default-200">
              <Card.Header className="p-8 pb-6">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Card.Title className="text-2xl font-bold tracking-tight text-foreground">
                      {t('auth.login.welcomeBack')}
                    </Card.Title>
                    <Chip className="gap-1 bg-default-100 text-xs">
                      <Sparkles className="h-3 w-3" />
                      {tCommon('brand.version')}
                    </Chip>
                  </div>
                  <Card.Description className="text-sm text-default-500">
                    {t('auth.login.description')}
                  </Card.Description>
                </div>
              </Card.Header>

              <Card.Content className="p-8 pt-0">
                <Form
                  onSubmit={submit}
                  validationErrors={errors}
                  validationBehavior="aria"
                  className="space-y-6"
                >
                  <div className="space-y-4">
                    {/* Email Field (sent as 'username' to Django) */}
                    <TextField name="username" className="space-y-2 w-full">
                      <Label className="text-sm font-medium text-default-700">{t('auth.login.emailLabel')}</Label>
                      <div className="relative w-full">
                        <User className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-default-400 z-10" />
                        <Input
                          type="email"
                          placeholder={t('auth.login.emailPlaceholder')}
                          autoComplete="email"
                          required
                          value={data.username}
                          onChange={(e) => setData('username', e.target.value)}
                          className="w-full pl-10 h-11 bg-default-100 border-default-200"
                        />
                      </div>
                      <FieldError />
                    </TextField>

                    {/* Password Field */}
                    <TextField name="password" className="space-y-2 w-full">
                      <div className="flex items-center justify-between">
                        <Label className="text-sm font-medium text-default-700">{t('auth.login.passwordLabel')}</Label>
                        <Link
                          href="/auth/forgot-password/"
                          className="text-xs text-default-500 hover:text-primary transition-colors"
                        >
                          {t('auth.login.forgotPassword')}
                        </Link>
                      </div>
                      <div className="relative w-full">
                        <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-default-400 z-10" />
                        <Input
                          type={showPassword ? 'text' : 'password'}
                          placeholder={t('auth.login.passwordPlaceholder')}
                          autoComplete="current-password"
                          required
                          value={data.password}
                          onChange={(e) => setData('password', e.target.value)}
                          className="w-full pl-10 pr-10 h-11 font-mono tracking-wider bg-default-100 border-default-200"
                        />
                        <button
                          type="button"
                          onClick={() => setShowPassword(!showPassword)}
                          className="absolute right-3 top-1/2 transform -translate-y-1/2 text-default-400 hover:text-default-600 transition-colors"
                          tabIndex={-1}
                        >
                          {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                        </button>
                      </div>
                      <FieldError />
                    </TextField>
                  </div>

                  {/* Remember Me */}
                  <div className="space-y-2">
                    <Checkbox
                      isSelected={data.remember_me}
                      onChange={(isSelected) => setData('remember_me', isSelected)}
                    >
                      <span className="text-sm text-default-600">{t('auth.login.rememberMe')}</span>
                    </Checkbox>
                    {data.remember_me && (
                      <p className="text-xs text-default-400 ml-6">
                        {t('auth.login.rememberMeHelp')}
                      </p>
                    )}
                  </div>

                  {/* Error Message */}
                  {errors.__all__ && (
                    <div className={`p-3 rounded-lg text-sm border ${
                      needs_verification
                        ? 'bg-warning-50 border-warning-200 text-warning-700'
                        : 'bg-danger-50 border-danger-200 text-danger-700'
                    }`}>
                      <div className="flex items-center gap-2">
                        <AlertCircle className="h-4 w-4 flex-shrink-0" />
                        <span>{errors.__all__}</span>
                      </div>
                      {needs_verification && (
                        <div className="mt-2 ml-6">
                          <Link
                            href={`/auth/verify-email/${verification_email ? `?email=${encodeURIComponent(verification_email)}` : ''}`}
                            className="inline-flex items-center gap-1 font-medium text-primary hover:opacity-80"
                          >
                            {t('auth.login.verifyEmailLink', 'Verify your email now')}
                            <ArrowRight className="h-3.5 w-3.5" />
                          </Link>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Submit Button */}
                  <Button
                    type="submit"
                    variant="primary"
                    size="lg"
                    fullWidth
                    isLoading={isSubmitting}
                    loadingText={t('auth.login.submitting')}
                    isDisabled={!data.username || !data.password || data.password.length < 8}
                  >
                    <span>{t('auth.login.submit')}</span>
                    <ArrowRight className="h-4 w-4" />
                  </Button>
                </Form>
              </Card.Content>

              <Card.Footer className="flex justify-center p-6 pt-0">
                <p className="text-sm text-default-500">
                  {t('auth.login.noAccount')}{' '}
                  <Link
                    href="/auth/register/"
                    className="text-primary hover:opacity-80 font-medium"
                  >
                    {t('auth.login.signUp')}
                  </Link>
                </p>
              </Card.Footer>
            </Card>

            {/* Footer */}
            <div className="text-center text-sm text-default-400">
              <p>{t('auth.login.copyright', { year: new Date().getFullYear() })}</p>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
