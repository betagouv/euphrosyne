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
      <ErrorMessage
        id={`participation-${String(firstKey)}-messages`}
        errors={fieldErrors}
      />
    );
  }

  if (!secondKey) {
    if ("non_field_errors" in fieldErrors) {
      return (
        <ErrorMessage
          id={`participation-${String(firstKey)}-messages`}
          errors={fieldErrors.non_field_errors}
        />
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
        <ErrorMessage
          id={`participation-${String(firstKey)}-${String(secondKey)}-messages`}
          errors={secondFieldErrors}
        />
      );
    }
  }
}

export function ErrorMessage({ id, errors }: { id: string; errors: string[] }) {
  return (
    <div className="fr-messages-group" id={id} aria-live="polite">
      {errors.map((errorMsg, idx) => (
        <p className="fr-message fr-message--error" key={`${id}-error-${idx}`}>
          {errorMsg}
        </p>
      ))}
    </div>
  );
}
