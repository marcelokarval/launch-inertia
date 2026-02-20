/**
 * Register Page - Complete rewrite using AuthLayout, HeroUI components,
 * useAppForm, and PasswordInput.
 *
 * Fields: first_name, last_name, email, password, password_confirmation, terms
 */

import { Head, Link } from '@inertiajs/react'
import { useTranslation } from 'react-i18next'
import { Form, Checkbox, Link as HeroLink } from '@heroui/react'
import { User, Mail, ArrowRight } from 'lucide-react'
import AuthLayout from '@/layouts/AuthLayout'
import { InputField, PasswordInput, FormErrorBanner, Button } from '@/components/ui'
import { useAppForm } from '@/hooks/useAppForm'

interface Props {
  errors?: Record<string, string>
}

export default function Register({ errors = {} }: Props) {
  const { t } = useTranslation()

  const {
    data,
    setData,
    submit,
    isSubmitting,
  } = useAppForm({
    initialData: {
      first_name: '' as string,
      last_name: '' as string,
      email: '' as string,
      password: '' as string,
      password_confirmation: '' as string,
      terms_accepted: false as boolean,
    },
    url: '/auth/register/',
    method: 'post',
  })

  const allFieldsFilled =
    data.first_name &&
    data.last_name &&
    data.email &&
    data.password &&
    data.password_confirmation &&
    data.terms_accepted

  return (
    <AuthLayout
      title={t('auth.register.title')}
      subtitle={t('auth.register.subtitle')}
    >
      <Head title={t('auth.register.pageTitle')} />

      <Form
        onSubmit={submit}
        validationErrors={errors}
        validationBehavior="aria"
        className="space-y-6"
      >
        {/* General error */}
        <FormErrorBanner message={errors.__all__} />

        {/* Name fields */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <InputField
            name="first_name"
            label={t('auth.register.firstNameLabel')}
            placeholder={t('auth.register.firstNamePlaceholder')}
            value={data.first_name as string}
            onChange={(e) => setData('first_name', e.target.value)}
            error={errors.first_name}
            required
            autoComplete="given-name"
            startContent={<User className="h-4 w-4" />}
          />
          <InputField
            name="last_name"
            label={t('auth.register.lastNameLabel')}
            placeholder={t('auth.register.lastNamePlaceholder')}
            value={data.last_name as string}
            onChange={(e) => setData('last_name', e.target.value)}
            error={errors.last_name}
            required
            autoComplete="family-name"
          />
        </div>

        {/* Email */}
        <InputField
          name="email"
          label={t('auth.register.emailLabel')}
          type="email"
          placeholder={t('auth.register.emailPlaceholder')}
          value={data.email as string}
          onChange={(e) => setData('email', e.target.value)}
          error={errors.email}
          required
          autoComplete="email"
          startContent={<Mail className="h-4 w-4" />}
        />

        {/* Password */}
        <PasswordInput
          name="password"
          label={t('auth.register.passwordLabel')}
          value={data.password as string}
          onChange={(e) => setData('password', e.target.value)}
          error={errors.password}
          required
          autoComplete="new-password"
          showStrength
        />

        {/* Password confirmation */}
        <PasswordInput
          name="password_confirmation"
          label={t('auth.register.confirmPasswordLabel')}
          value={data.password_confirmation as string}
          onChange={(e) => setData('password_confirmation', e.target.value)}
          error={errors.password_confirmation}
          required
          autoComplete="new-password"
        />

        {/* Terms */}
        <div className="space-y-2">
          <Checkbox
            isSelected={data.terms_accepted as boolean}
            onChange={(isSelected) => setData('terms_accepted', isSelected)}
            isRequired
          >
            <span className="text-sm text-default-600">
              {t('auth.register.termsAgree')}{' '}
              <HeroLink
                href="#"
                className="text-primary hover:opacity-80 font-medium text-sm"
                target="_blank"
                rel="noopener noreferrer"
              >
                {t('auth.register.termsOfService')}
              </HeroLink>{' '}
              {t('auth.register.and')}{' '}
              <HeroLink
                href="#"
                className="text-primary hover:opacity-80 font-medium text-sm"
                target="_blank"
                rel="noopener noreferrer"
              >
                {t('auth.register.privacyPolicy')}
              </HeroLink>
            </span>
          </Checkbox>
          <FormErrorBanner message={errors.terms_accepted} />
        </div>

        {/* Submit */}
        <Button
          type="submit"
          variant="primary"
          size="lg"
          fullWidth
          isLoading={isSubmitting}
          loadingText={t('auth.register.submitting')}
          isDisabled={!allFieldsFilled}
        >
          <span>{t('auth.register.submit')}</span>
          <ArrowRight className="h-4 w-4" />
        </Button>

        {/* Login link */}
        <p className="text-center text-sm text-default-500">
          {t('auth.register.hasAccount')}{' '}
          <Link
            href="/auth/login/"
            className="text-primary hover:opacity-80 font-medium"
          >
            {t('auth.register.signIn')}
          </Link>
        </p>
      </Form>
    </AuthLayout>
  )
}
