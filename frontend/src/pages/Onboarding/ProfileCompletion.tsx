/**
 * Onboarding Step 3: Profile Completion
 */

import { Head } from '@inertiajs/react'
import {
  Form,
  TextField,
  Input,
  Label,
  FieldError,
  TextArea,
} from '@heroui/react'
import { Button, FormErrorBanner } from '@/components/ui'
import { User, Phone, Building, FileText } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import OnboardingLayout from '@/layouts/OnboardingLayout'
import { useAppForm } from '@/hooks/useAppForm'

interface Props {
  profile_data?: {
    first_name: string
    last_name: string
    phone: string
    company: string
    bio: string
  }
  errors?: Record<string, string[]>
}

export default function ProfileCompletion({ profile_data, errors = {} }: Props) {
  const { t } = useTranslation()

  const { data, setData, submit, isSubmitting } = useAppForm({
    initialData: {
      first_name: profile_data?.first_name || '',
      last_name: profile_data?.last_name || '',
      phone: profile_data?.phone || '',
      company: profile_data?.company || '',
      bio: profile_data?.bio || '',
    },
    url: '/onboarding/profile-completion/',
    method: 'post',
  })

  const profileError = errors.profile?.[0]
  const canSubmit = data.first_name.trim() && data.last_name.trim() && data.phone.trim()

  return (
    <OnboardingLayout currentStep={3} title={t('onboarding.profile.title')}>
      <Head title={t('onboarding.profile.pageTitle')} />

      <div className="space-y-6">
        <p className="text-sm text-default-600">
          {t('onboarding.profile.instruction')}
        </p>

        {/* Error banner */}
        <FormErrorBanner message={profileError} />

        <Form
          onSubmit={submit}
          validationErrors={errors}
          validationBehavior="aria"
          className="space-y-5"
        >
          {/* Name fields */}
          <div className="grid grid-cols-2 gap-4">
            <TextField name="first_name" className="space-y-2">
              <Label className="text-sm font-medium text-default-700">
                {t('onboarding.profile.firstNameLabel')} <span className="text-danger">*</span>
              </Label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-default-400 z-10" />
                <Input
                  type="text"
                  value={data.first_name}
                  onChange={(e) => setData('first_name', e.target.value)}
                  placeholder={t('onboarding.profile.firstNamePlaceholder')}
                  required
                  className="pl-10 w-full h-10 bg-default-100 border-default-200"
                />
              </div>
              <FieldError />
            </TextField>

            <TextField name="last_name" className="space-y-2">
              <Label className="text-sm font-medium text-default-700">
                {t('onboarding.profile.lastNameLabel')} <span className="text-danger">*</span>
              </Label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-default-400 z-10" />
                <Input
                  type="text"
                  value={data.last_name}
                  onChange={(e) => setData('last_name', e.target.value)}
                  placeholder={t('onboarding.profile.lastNamePlaceholder')}
                  required
                  className="pl-10 w-full h-10 bg-default-100 border-default-200"
                />
              </div>
              <FieldError />
            </TextField>
          </div>

          {/* Phone */}
          <TextField name="phone" className="space-y-2">
            <Label className="text-sm font-medium text-default-700">
              {t('onboarding.profile.phoneLabel')} <span className="text-danger">*</span>
            </Label>
            <div className="relative">
              <Phone className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-default-400 z-10" />
              <Input
                type="tel"
                value={data.phone}
                onChange={(e) => setData('phone', e.target.value)}
                placeholder={t('onboarding.profile.phonePlaceholder')}
                required
                className="pl-10 w-full h-10 bg-default-100 border-default-200"
              />
            </div>
            <FieldError />
          </TextField>

          {/* Company (optional) */}
          <TextField name="company" className="space-y-2">
            <Label className="text-sm font-medium text-default-700">
              {t('onboarding.profile.companyLabel')}
            </Label>
            <div className="relative">
              <Building className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-default-400 z-10" />
              <Input
                type="text"
                value={data.company}
                onChange={(e) => setData('company', e.target.value)}
                placeholder={t('onboarding.profile.companyPlaceholder')}
                className="pl-10 w-full h-10 bg-default-100 border-default-200"
              />
            </div>
            <FieldError />
          </TextField>

          {/* Bio (optional) */}
          <TextField name="bio" className="space-y-2">
            <Label className="text-sm font-medium text-default-700">
              {t('onboarding.profile.bioLabel')}
            </Label>
            <div className="relative">
              <FileText className="absolute left-3 top-3 h-4 w-4 text-default-400 z-10" />
              <TextArea
                value={data.bio}
                onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setData('bio', e.target.value)}
                placeholder={t('onboarding.profile.bioPlaceholder')}
                rows={3}
                maxLength={500}
                className="pl-10"
              />
            </div>
            <FieldError />
            <p className="text-xs text-default-400 text-right">{data.bio.length}/500</p>
          </TextField>

          {/* Submit */}
          <Button
            type="submit"
            variant="primary"
            fullWidth
            isLoading={isSubmitting}
            loadingText={t('onboarding.profile.submitting')}
            isDisabled={!canSubmit}
          >
            {t('onboarding.profile.submit')}
          </Button>
        </Form>
      </div>
    </OnboardingLayout>
  )
}
