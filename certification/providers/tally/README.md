# Tally provider

This provider handles Tally webhook submissions for quiz certifications. It validates
the webhook signature, extracts the quiz result, and creates the corresponding
`QuizResult` and `CertificationNotification` entries.

## Endpoint

- `POST /certification/hooks/tally` (registered in `certification/urls.py` when the
  `radiation_protection` app is installed).
- The implementation lives in `certification/providers/tally/hooks.py` and is
  wrapped by `radiation_protection/tally.py` to inject the secret key.

## Required headers

- `Tally-Signature`: base64-encoded HMAC-SHA256 of the raw request body using the
  shared secret key.
- `Euphrosyne-Certification`: the `Certification.name` to attach the result to.
- `Euphrosyne-QuizUrl`: the `QuizCertification.url` that identifies the quiz.

## Payload expectations (Tally)

The webhook payload is parsed into `TallyWebhookData`. These fields are required:

- Hidden field labeled `email` (type `HIDDEN_FIELDS`) for `user_email`.
- Calculated field labeled `Score` (type `CALCULATED_FIELDS`) for the numeric score.

Optional fields used to update user names when present:

- `First name`
- `Last name`

If the email or score is missing, the webhook returns `400`.

## Secret key and signature validation

The secret key is used to verify the webhook signature:

- Environment variable: `RADIATION_PROTECTION_TALLY_SECRET_KEY`
- The wrapper `radiation_protection/tally.py` passes it into
  `certification.providers.tally.hooks.tally_webhook(request, secret_key)`.
- Signature validation logic (see `_validate_signature` in `hooks.py`) computes
  `base64(hmac_sha256(secret_key, request.body))` and compares it to
  `Tally-Signature` with `hmac.compare_digest`.

If the signature is invalid, the webhook returns `403`. If the signature header is
missing, the request is considered invalid and should be rejected by the caller.

## Side effects

On success:

- Creates a `QuizResult` for the user and quiz.
- Creates a `CertificationNotification` of type `SUCCESS` or `RETRY` based on the
  passing score.
