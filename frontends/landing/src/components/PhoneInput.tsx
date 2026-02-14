import { useId } from 'react';
import { PhoneInput as ReactPhoneInput } from 'react-international-phone';
import 'react-international-phone/style.css';

interface PhoneInputProps {
  label: string;
  value: string;
  onChange: (phone: string) => void;
  error?: string;
  disabled?: boolean;
}

/**
 * International phone number input.
 * Wraps react-international-phone with landing design tokens.
 * Default country: BR (Brazil).
 */
export default function PhoneInput({
  label,
  value,
  onChange,
  error,
  disabled = false,
}: PhoneInputProps) {
  const inputId = useId();

  return (
    <div className="w-full">
      <label
        htmlFor={inputId}
        className="mb-1.5 block text-sm font-medium text-[var(--color-text-primary)]"
      >
        {label}
      </label>
      <div
        className={`phone-input-wrapper rounded-lg border transition-colors duration-150 ${
          error
            ? 'border-[var(--color-error)]'
            : 'border-[var(--color-border)] focus-within:ring-2 focus-within:ring-[var(--color-border-focus)]'
        }`}
      >
        <ReactPhoneInput
          defaultCountry="br"
          value={value}
          onChange={onChange}
          disabled={disabled}
          inputProps={{ id: inputId }}
          inputClassName="phone-input-field"
          countrySelectorStyleProps={{
            buttonClassName: 'phone-country-selector',
          }}
        />
      </div>
      {error && (
        <p className="mt-1 text-sm text-[var(--color-error)]">{error}</p>
      )}
    </div>
  );
}
