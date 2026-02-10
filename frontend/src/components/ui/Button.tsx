/**
 * Enhanced Button with loading state.
 *
 * Wraps HeroUI Button with standardised variants and a loading spinner.
 */

import { forwardRef } from 'react'
import { Button as HeroButton, Spinner } from '@heroui/react'
import { tv, type VariantProps } from 'tailwind-variants'

const buttonStyles = tv({
  base: 'font-medium transition-all inline-flex items-center justify-center gap-2',
  variants: {
    variant: {
      primary:
        'bg-gradient-primary text-white shadow-lg shadow-purple-500/25 hover:opacity-90',
      secondary:
        'bg-default-100 text-foreground hover:bg-default-200',
      outline:
        'border border-default-300 bg-transparent text-default-700 hover:bg-default-100',
      ghost:
        'bg-transparent text-default-700 hover:bg-default-100',
      danger:
        'bg-danger hover:bg-danger-600 text-white shadow-lg shadow-danger/25',
    },
    size: {
      sm: 'h-9 px-3 text-sm rounded-lg',
      md: 'h-11 px-5 text-sm rounded-lg',
      lg: 'h-12 px-6 text-base rounded-xl',
    },
    fullWidth: {
      true: 'w-full',
    },
  },
  defaultVariants: {
    variant: 'primary',
    size: 'md',
    fullWidth: false,
  },
})

export type ButtonVariants = VariantProps<typeof buttonStyles>

export interface ButtonProps
  extends Omit<React.ComponentProps<typeof HeroButton>, 'size' | 'variant'>,
    ButtonVariants {
  isLoading?: boolean
  loadingText?: string
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      children,
      className,
      variant,
      size,
      fullWidth,
      isLoading = false,
      loadingText,
      isDisabled,
      ...props
    },
    ref,
  ) => {
    return (
      <HeroButton
        ref={ref}
        className={buttonStyles({ variant, size, fullWidth, className: className as string })}
        isDisabled={isDisabled || isLoading}
        {...props}
      >
        {isLoading ? (
          <>
            <Spinner size="sm" color="current" />
            {loadingText && <span>{loadingText}</span>}
          </>
        ) : (
          children
        )}
      </HeroButton>
    )
  },
)

Button.displayName = 'Button'
