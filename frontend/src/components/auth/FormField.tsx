import type { InputHTMLAttributes } from "react";

type FormFieldProps = InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  error?: string;
};

export function FormField({ label, error, id, ...inputProps }: FormFieldProps) {
  const fieldId = id ?? inputProps.name;
  const errorId = error && fieldId ? `${fieldId}-error` : undefined;

  return (
    <label className="form-field" htmlFor={fieldId}>
      <span>{label}</span>
      <input
        {...inputProps}
        id={fieldId}
        aria-invalid={Boolean(error)}
        aria-describedby={errorId}
      />
      {error ? (
        <small className="form-error" id={errorId}>
          {error}
        </small>
      ) : null}
    </label>
  );
}
