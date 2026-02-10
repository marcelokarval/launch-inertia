/**
 * Profile Settings page.
 *
 * Backend sends: user.to_dict() + profile.to_dict()
 * ProfileForm accepts: first_name, last_name, phone, bio, avatar,
 *   address_line1, address_line2, city, state, postal_code, country
 *
 * POSTs to /settings/profile/ with forceFormData: true.
 */

import { Head } from '@inertiajs/react'
import { useTranslation } from 'react-i18next'
import DashboardLayout from '@/layouts/DashboardLayout'
import { TextField, Input, Label, FieldError, Form, TextArea } from '@heroui/react'
import { User as UserIcon, Phone } from 'lucide-react'
import { Button } from '@/components/ui'
import { useAppForm } from '@/hooks/useAppForm'
import type { User, UserProfile } from '@/types'

/**
 * Props match User.to_dict() and Profile.to_dict() output.
 */
interface ProfileProps {
  user: Pick<User, 'id' | 'email' | 'name' | 'first_name' | 'last_name'>
  profile: Pick<UserProfile, 'id' | 'phone' | 'bio' | 'avatar_url' | 'address'> | null
  errors?: Record<string, string>
}

export default function Profile({ user, profile, errors = {} }: ProfileProps) {
  const { t } = useTranslation()
  const { data, setData, submit, isSubmitting } = useAppForm({
    initialData: {
      first_name: user.first_name || '',
      last_name: user.last_name || '',
      phone: profile?.phone || '',
      bio: profile?.bio || '',
      state: profile?.address?.state || '',
      city: profile?.address?.city || '',
    },
    url: '/settings/profile/',
    method: 'post',
  })

  return (
    <DashboardLayout title={t('settings.profile.pageTitle')}>
      <Head title={t('settings.profile.pageTitle')} />

      <div className="max-w-2xl mx-auto">
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-foreground">
            {t('settings.profile.title')}
          </h2>
          <p className="mt-1 text-default-500">
            {t('settings.profile.description')}
          </p>
        </div>

        <div className="bg-content1 rounded-lg shadow-sm border border-default-200">
          <div className="p-6">
            <Form
              onSubmit={submit}
              validationErrors={errors}
              className="space-y-6"
            >
              <div className="flex items-center gap-6 pb-6 border-b border-divider">
                <div className="w-20 h-20 rounded-full bg-primary/10 flex items-center justify-center">
                  {profile?.avatar_url ? (
                    <img
                      src={profile.avatar_url}
                      alt={user.name}
                      className="w-20 h-20 rounded-full object-cover"
                    />
                  ) : (
                    <UserIcon className="w-10 h-10 text-primary" />
                  )}
                </div>
                <div>
                  <h3 className="font-semibold text-foreground">
                    {user.name}
                  </h3>
                  <p className="text-sm text-default-500">{user.email}</p>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <TextField name="first_name" className="space-y-2">
                  <Label>{t('settings.profile.firstNameLabel')}</Label>
                  <div className="relative">
                    <UserIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-default-400 z-10" />
                    <Input
                      type="text"
                      value={data.first_name}
                      onChange={(e) => setData('first_name', e.target.value)}
                      className="pl-10"
                    />
                  </div>
                  <FieldError />
                </TextField>

                <TextField name="last_name" className="space-y-2">
                  <Label>{t('settings.profile.lastNameLabel')}</Label>
                  <Input
                    type="text"
                    value={data.last_name}
                    onChange={(e) => setData('last_name', e.target.value)}
                  />
                  <FieldError />
                </TextField>
              </div>

              <TextField name="phone" className="space-y-2">
                <Label>{t('settings.profile.phoneLabel')}</Label>
                <div className="relative">
                  <Phone className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-default-400 z-10" />
                  <Input
                    type="tel"
                    value={data.phone}
                    onChange={(e) => setData('phone', e.target.value)}
                    className="pl-10"
                    placeholder={t('settings.profile.phonePlaceholder')}
                  />
                </div>
                <FieldError />
              </TextField>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <TextField name="state" className="space-y-2">
                  <Label>{t('settings.profile.stateLabel')}</Label>
                  <Input
                    type="text"
                    value={data.state}
                    onChange={(e) => setData('state', e.target.value)}
                  />
                  <FieldError />
                </TextField>

                <TextField name="city" className="space-y-2">
                  <Label>{t('settings.profile.cityLabel')}</Label>
                  <Input
                    type="text"
                    value={data.city}
                    onChange={(e) => setData('city', e.target.value)}
                  />
                  <FieldError />
                </TextField>
              </div>

              <TextField name="bio" className="space-y-2">
                <Label>{t('settings.profile.bioLabel')}</Label>
                <TextArea
                  value={data.bio}
                  onChange={(e) => setData('bio', e.target.value)}
                  rows={3}
                  placeholder={t('settings.profile.bioPlaceholder')}
                />
                <FieldError />
              </TextField>

              <div className="pt-4">
                <Button
                  type="submit"
                  variant="primary"
                  isLoading={isSubmitting}
                  loadingText={t('settings.profile.submitting')}
                >
                  {t('settings.profile.submit')}
                </Button>
              </div>
            </Form>
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
}
