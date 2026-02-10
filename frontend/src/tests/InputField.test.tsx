import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { InputField } from '@/components/ui/InputField'

// Mock HeroUI components
vi.mock('@heroui/react', async () => ({
  TextField: ({ children, name, isInvalid, isRequired, isDisabled, className }: any) => (
    <div
      data-testid={`textfield-${name}`}
      data-invalid={isInvalid}
      data-required={isRequired}
      data-disabled={isDisabled}
      className={className}
    >
      {children}
    </div>
  ),
  Input: ({ type, placeholder, value, onChange, className, autoComplete }: any) => (
    <input
      type={type}
      placeholder={placeholder}
      value={value}
      onChange={onChange}
      className={className}
      autoComplete={autoComplete}
      data-testid="hero-input"
    />
  ),
  Label: ({ children, className }: any) => (
    <label className={className}>{children}</label>
  ),
  FieldError: () => <span data-testid="field-error" />,
}))

describe('InputField', () => {
  const defaultProps = {
    name: 'email',
    value: '',
    onChange: vi.fn(),
  }

  it('renders without label when not provided', () => {
    render(<InputField {...defaultProps} />)
    expect(screen.queryByRole('label')).not.toBeInTheDocument()
  })

  it('renders the label when provided', () => {
    render(<InputField {...defaultProps} label="Email" />)
    expect(screen.getByText('Email')).toBeInTheDocument()
  })

  it('renders the input with correct placeholder', () => {
    render(<InputField {...defaultProps} placeholder="Enter email" />)
    expect(screen.getByPlaceholderText('Enter email')).toBeInTheDocument()
  })

  it('passes value to the input', () => {
    render(<InputField {...defaultProps} value="test@test.com" />)
    const input = screen.getByTestId('hero-input')
    expect(input).toHaveValue('test@test.com')
  })

  it('calls onChange when typing', async () => {
    const handleChange = vi.fn()
    const user = userEvent.setup()
    render(<InputField {...defaultProps} onChange={handleChange} />)

    await user.type(screen.getByTestId('hero-input'), 'a')
    expect(handleChange).toHaveBeenCalled()
  })

  it('shows error message when error is provided', () => {
    render(<InputField {...defaultProps} error="Required field" />)
    expect(screen.getByText('Required field')).toBeInTheDocument()
  })

  it('shows FieldError component when no error', () => {
    render(<InputField {...defaultProps} />)
    expect(screen.getByTestId('field-error')).toBeInTheDocument()
  })

  it('does not show FieldError when error is provided', () => {
    render(<InputField {...defaultProps} error="Something wrong" />)
    expect(screen.queryByTestId('field-error')).not.toBeInTheDocument()
  })

  it('marks TextField as invalid when error exists', () => {
    render(<InputField {...defaultProps} error="Bad input" />)
    const tf = screen.getByTestId('textfield-email')
    expect(tf.dataset.invalid).toBe('true')
  })

  it('marks TextField as required', () => {
    render(<InputField {...defaultProps} required />)
    const tf = screen.getByTestId('textfield-email')
    expect(tf.dataset.required).toBe('true')
  })

  it('marks TextField as disabled', () => {
    render(<InputField {...defaultProps} disabled />)
    const tf = screen.getByTestId('textfield-email')
    expect(tf.dataset.disabled).toBe('true')
  })

  it('renders startContent', () => {
    render(
      <InputField
        {...defaultProps}
        startContent={<span data-testid="start">@</span>}
      />,
    )
    expect(screen.getByTestId('start')).toBeInTheDocument()
  })

  it('renders endContent', () => {
    render(
      <InputField
        {...defaultProps}
        endContent={<span data-testid="end">!</span>}
      />,
    )
    expect(screen.getByTestId('end')).toBeInTheDocument()
  })

  it('uses text type by default', () => {
    render(<InputField {...defaultProps} />)
    const input = screen.getByTestId('hero-input')
    expect(input).toHaveAttribute('type', 'text')
  })

  it('accepts custom type', () => {
    render(<InputField {...defaultProps} type="password" />)
    const input = screen.getByTestId('hero-input')
    expect(input).toHaveAttribute('type', 'password')
  })
})
