import { ValidationDataError } from "../participation.service";

export default function FieldError<T>({
  errors,
  firstKey,
  secondKey,
}: {
  errors: ValidationDataError<T> | null;
  firstKey: keyof T;
  secondKey?: string;
}) {
  const fieldErrors = errors?.[firstKey];
  if (!fieldErrors) {
    return null;
  }

  if (Array.isArray(fieldErrors)) {
    return (
      <div
        className="fr-messages-group"
        id={`participation-${String(firstKey)}-messages`}
        aria-live="polite"
      >
        {fieldErrors.map((errorMsg, idx) => (
          <p
            className="fr-message fr-message--error"
            key={`participation-${String(firstKey)}-error-${idx}`}
          >
            {errorMsg}
          </p>
        ))}
      </div>
    );
  }

  if (!secondKey) {
    if ("non_field_errors" in fieldErrors) {
      return (
        <div
          className="fr-messages-group"
          id={`participation-${String(firstKey)}-messages`}
          aria-live="polite"
        >
          {fieldErrors.non_field_errors.map((errorMsg, idx) => (
            <p
              className="fr-message fr-message--error"
              key={`participation-${String(firstKey)}-non-field-error-${idx}`}
            >
              {errorMsg}
            </p>
          ))}
        </div>
      );
    }
    return null;
  }

  if (
    typeof fieldErrors === "object" &&
    fieldErrors !== null &&
    !Array.isArray(fieldErrors)
  ) {
    const secondFieldErrors = (fieldErrors as Record<string, string[]>)[
      secondKey
    ];

    if (Array.isArray(secondFieldErrors)) {
      return (
        <div
          className="fr-messages-group"
          id={`participation-${String(firstKey)}-${String(secondKey)}-messages`}
          aria-live="polite"
        >
          {secondFieldErrors.map((errorMsg, idx) => (
            <p
              className="fr-message fr-message--error"
              key={`participation-${String(firstKey)}-${String(secondKey)}-error-${idx}`}
            >
              {errorMsg}
            </p>
          ))}
        </div>
      );
    }
  }
}
