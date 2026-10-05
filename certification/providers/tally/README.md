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

Missing, empty, incorrect or malformed signatures return `403` with
`{"error": "Invalid signature"}`. The comparison uses the canonical base64 value:
non-ASCII characters, invalid base64, incorrect padding and extra whitespace are
rejected without decoding untrusted input. Changing even the whitespace in the
raw body invalidates the signature; JSON must not be reserialized before checking.

An absent (`None`) or empty signing secret disables processing and returns `503`
with `{"error": "Webhook unavailable"}`. The server logs that the signing secret
is not configured, without logging its value, the signature or the payload. Both
the shared handler and the exposed wrapper fail closed. Authentication failures
are handled before JSON parsing, user name updates, quiz results or notifications.

## CSRF findings and security qualification (issue #2041)

The Snyk Code report of 30 September 2026 identifies two `csrf_exempt` decorators
(CWE-352, medium severity): in `radiation_protection/tally.py` and in
`certification/providers/tally/hooks.py`. These refer to one processing path:
the URL resolves to the radioprotection wrapper, which supplies the configured
secret to the shared provider handler. The wrapper exemption allows the incoming
server-to-server POST through Django's CSRF middleware; the provider exemption
expresses the same authentication contract for that reusable handler.

Tally cannot supply a Django browser CSRF token. Instead, the webhook requires
the base64 HMAC-SHA256 signature of the raw body with the shared signing secret,
as described in [Tally's webhook documentation](https://tally.so/help/webhooks).
The signature is compared with `hmac.compare_digest` before any side effect.
A user's session, cookies, staff status or CSRF token do not authorize a webhook:
unsigned requests are refused, including requests carrying a valid user session.
Removing either decorator alone does not establish the appropriate webhook
authentication mechanism.

The exemptions alone therefore do not demonstrate exploitable browser CSRF.
Forging an accepted body requires knowledge or compromise of the signing secret,
control of the trusted Tally configuration, or a bypass of the validation path.
An absent or empty secret previously caused uncontrolled failures or allowed
signatures using a known empty key; this handler now refuses both configurations.

The HMAC covers the body only, not the `Euphrosyne-Certification` and
`Euphrosyne-QuizUrl` headers. It does not prevent replay: an attacker who obtains a
valid signed payload could resend it, potentially with different routing headers.
Those limitations remain outside this targeted CSRF/signature correction and
must be considered in the homologation assessment.

### Deployment prerequisites and evidence

- Configure a strong, non-empty signing secret in Tally and the matching
  `RADIATION_PROTECTION_TALLY_SECRET_KEY` in Euphrosyne (including any
  `RADIATION_PROTECTION_SETTINGS` override). Do not expose it to browsers, logs or
  version control; rotate it in both systems if compromised.
- Serve the webhook over HTTPS and preserve the body bytes and configured
  headers through the reverse proxy. Restrict access to Tally configuration and
  validate the intended certification and quiz URL there.
- Verify in the deployed environment that a signed submission succeeds and that
  missing/incorrect signatures and missing/empty secrets yield `403`/`503` without
  writes. Investigate the configuration diagnostic when `503` is returned.
- Automated regression tests in `certification/tests/test_tally_security.py`
  calculate real signatures and exercise the exposed URL with CSRF checks enabled,
  both anonymously and with a session. They cover altered bodies, malformed
  signatures, disabled secrets and the absence of parsing or side effects on refusal.
- For the dossier due on 30 November 2026 (homologation on 15 December), rerun
  Snyk Code on the final commit and retain the report, commit SHA and assessment of
  both findings. A documented exemption can only be considered after verifying
  these protections. This documentation is a qualification of the findings, not
  evidence of a successful new Snyk audit or of production configuration checks.

## Side effects

On success:

- Creates a `QuizResult` for the user and quiz.
- Creates a `CertificationNotification` of type `SUCCESS` or `RETRY` based on the
  passing score.
