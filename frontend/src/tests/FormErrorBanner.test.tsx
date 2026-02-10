import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { FormErrorBanner } from '@/components/ui/FormErrorBanner'

// Mock lucide-react icons
vi.mock('lucide-react', () => ({
  AlertCircle: ({ className }: any) => (
    <svg data-testid="alert-icon" className={className} />
  ),
  X: ({ className }: any) => (
    <svg data-testid="x-icon" className={className} />
  ),
}))

describe('FormErrorBanner', () => {
  it('renders nothing when message is null', () => {
    const { container } = render(<FormErrorBanner message={null} />)
    expect(container.firstChild).toBeNull()
  })

  it('renders nothing when message is undefined', () => {
    const { container } = render(<FormErrorBanner />)
    expect(container.firstChild).toBeNull()
  })

  it('renders nothing when message is empty string', () => {
    const { container } = render(<FormErrorBanner message="" />)
    // empty string is falsy
    expect(container.firstChild).toBeNull()
  })

  it('renders the error message', () => {
    render(<FormErrorBanner message="Something went wrong" />)
    expect(screen.getByText('Something went wrong')).toBeInTheDocument()
  })

  it('has role="alert" for accessibility', () => {
    render(<FormErrorBanner message="Error" />)
    expect(screen.getByRole('alert')).toBeInTheDocument()
  })

  it('shows dismiss button by default', () => {
    render(<FormErrorBanner message="Error" />)
    // dismiss button has aria-label from t('actions.dismiss') which returns the key
    expect(screen.getByLabelText('actions.dismiss')).toBeInTheDocument()
  })

  it('hides dismiss button when dismissible=false', () => {
    render(<FormErrorBanner message="Error" dismissible={false} />)
    expect(screen.queryByLabelText('actions.dismiss')).not.toBeInTheDocument()
  })

  it('dismisses the banner when clicking the X button', async () => {
    const user = userEvent.setup()
    render(<FormErrorBanner message="Error" />)

    expect(screen.getByText('Error')).toBeInTheDocument()

    await user.click(screen.getByLabelText('actions.dismiss'))

    expect(screen.queryByText('Error')).not.toBeInTheDocument()
  })

  it('applies custom className', () => {
    render(<FormErrorBanner message="Error" className="mt-4" />)
    const alert = screen.getByRole('alert')
    expect(alert.className).toContain('mt-4')
  })

  it('renders alert icon', () => {
    render(<FormErrorBanner message="Error" />)
    expect(screen.getByTestId('alert-icon')).toBeInTheDocument()
  })
})
