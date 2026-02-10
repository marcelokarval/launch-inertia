/**
 * useAppForm - Custom wrapper around Inertia's useForm.
 *
 * Standardises form handling across the app:
 * - Always sends forceFormData: true (Django expects form-encoded POST)
 * - Provides a typed handleChange helper
 * - Exposes an `isSubmitting` alias for `processing`
 */

import { useForm, type InertiaFormProps } from '@inertiajs/react'
import type { FormDataType, FormDataKeys, FormDataValues } from '@inertiajs/core'

interface UseAppFormOptions<TForm extends FormDataType<TForm>> {
  initialData: TForm
  url: string
  method?: 'post' | 'put' | 'patch' | 'delete'
  onSuccess?: () => void
  onError?: () => void
  preserveScroll?: boolean
}

export function useAppForm<TForm extends FormDataType<TForm>>(
  options: UseAppFormOptions<TForm>,
) {
  const form = useForm<TForm>(options.initialData)

  const handleChange =
    <K extends FormDataKeys<TForm>>(field: K) =>
    (value: FormDataValues<TForm, K>) => {
      form.setData(field, value)
    }

  const submit = (e?: React.FormEvent) => {
    e?.preventDefault()
    const method = options.method || 'post'

    form[method](options.url, {
      forceFormData: true,
      preserveScroll: options.preserveScroll ?? true,
      onSuccess: options.onSuccess,
      onError: options.onError,
    })
  }

  return {
    ...form,
    handleChange,
    submit,
    isSubmitting: form.processing,
  }
}

export type { InertiaFormProps }
