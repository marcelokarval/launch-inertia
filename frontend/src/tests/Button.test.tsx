import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Button } from '@/components/ui/Button'

// Mock HeroUI components
vi.mock('@heroui/react', () => ({
  Button: ({
    children,
    className,
    isDisabled,
    onClick,
    ...props
  }: any) => (
    <button
      className={className}
      disabled={isDisabled}
      onClick={onClick}
      {...props}
    >
      {children}
    </button>
  ),
  Spinner: ({ size, color }: any) => (
    <span data-testid="spinner" data-size={size} data-color={color} />
  ),
}))

describe('Button', () => {
  it('renders children correctly', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByText('Click me')).toBeInTheDocument()
  })

  it('applies variant classes via tailwind-variants', () => {
    const { container } = render(<Button variant="danger">Delete</Button>)
    const button = container.querySelector('button')!
    expect(button.className).toContain('bg-danger')
  })

  it('applies size classes', () => {
    const { container } = render(<Button size="lg">Large</Button>)
    const button = container.querySelector('button')!
    expect(button.className).toContain('h-12')
  })

  it('applies fullWidth class', () => {
    const { container } = render(<Button fullWidth>Full</Button>)
    const button = container.querySelector('button')!
    expect(button.className).toContain('w-full')
  })

  it('shows spinner when isLoading', () => {
    render(<Button isLoading>Submit</Button>)
    expect(screen.getByTestId('spinner')).toBeInTheDocument()
    expect(screen.queryByText('Submit')).not.toBeInTheDocument()
  })

  it('shows loadingText alongside spinner', () => {
    render(
      <Button isLoading loadingText="Saving...">
        Submit
      </Button>,
    )
    expect(screen.getByTestId('spinner')).toBeInTheDocument()
    expect(screen.getByText('Saving...')).toBeInTheDocument()
  })

  it('disables button when isLoading', () => {
    const { container } = render(<Button isLoading>Submit</Button>)
    const button = container.querySelector('button')!
    expect(button).toBeDisabled()
  })

  it('disables button when isDisabled', () => {
    const { container } = render(<Button isDisabled>Submit</Button>)
    const button = container.querySelector('button')!
    expect(button).toBeDisabled()
  })

  it('fires onClick handler', async () => {
    const user = userEvent.setup()
    const handleClick = vi.fn()
    // Our mock renders a plain <button>, so we use onClick directly.
    // In production, HeroUI Button uses onPress internally.
    render(<Button onClick={handleClick}>Click</Button>)
    await user.click(screen.getByText('Click'))
    expect(handleClick).toHaveBeenCalledOnce()
  })

  it('uses default variant and size when none specified', () => {
    const { container } = render(<Button>Default</Button>)
    const button = container.querySelector('button')!
    // default variant is 'primary' — uses bg-gradient-primary
    expect(button.className).toContain('bg-gradient-primary')
    // default size is 'md' — h-11
    expect(button.className).toContain('h-11')
  })

  it('has correct displayName', () => {
    expect(Button.displayName).toBe('Button')
  })
})
