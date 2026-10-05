# PDF export image download policy

Issue: [#2040](https://github.com/betagouv/euphrosyne/issues/2040).
Baseline reviewed: `e953c584` (the issue's audit refers to `6743d0a4`).

## Flow qualification

The PDF export reads the run and checks project membership or laboratory admin
access before requesting storage information or downloading images. The existing
staff restriction on the admin-wrapped export route remains in effect.

`euphro_tools/download_urls.py` calls the configured `EUPHROSYNE_TOOLS_API_URL`
at `/images/projects/<slug>/signed-url`, with a backend JWT. The slug is encoded
as one path segment. Database input does not select the Tools API origin.
The returned `base_url` is external data, and must not itself establish trust.

`lab/objects/models.py` classifies stored image paths and constructs URLs:

| Source | Necessary destination | Policy |
| --- | --- | --- |
| Azure | Account endpoint returned by Tools API, normally `https://<account>.blob.core.windows.net` | Exact configured HTTPS origins in `PDF_EXPORT_AZURE_IMAGE_ORIGINS`; no wildcard or blanket Azure domain allowance |
| EROS direct | `EROS_BASE_IMAGE_URL`, with an `/iiif/` image path and EROS token | Exact scheme, host and effective port from this operator-controlled setting |
| EROS proxy | `EUPHROSYNE_TOOLS_API_URL`, under `/eros/iiif/`, with a Tools JWT | Used when `EROS_BASE_IMAGE_URL` is unset; exact configured scheme, host and effective port |
| POP | `https://iiif.prd.cloud.culture.fr` | HTTPS, this exact host, port 443 |

EROS identifiers are escaped before inserting them into the URL path.
POP image paths are attached to the fixed IIIF origin. Provider metadata
lookups (`eros.c2rmf.fr`, POP tabular API and manifests) are not called by the
PDF export's URL constructors; they are outside this export correction.

Every image request selects the policy for its own source. An Azure image
cannot use the EROS exception for an internal destination, or send its SAS token
to POP. The HTTP boundary validates the complete scheme/host/effective-port
tuple before issuing a request. Relative URLs, credentials in the authority,
fragments, invalid ports, control characters and ambiguous authorities are
rejected. Signed query strings are preserved.

Both the storage-information call and image downloads use
`allow_redirects=False`. Every non-2xx response, including same-origin and
relative redirects, is refused. No redirect target receives the JWT, EROS token
or SAS query. Timeouts remain 5 seconds for Tools API and 10 seconds for images.
Responses are closed, and failures produce an empty HTTP 502 response without
echoing or logging the URL, tokens, response body or upstream exception message.

## Deployment configuration

Set the exact account origins used by Tools API before deploying this change:

```sh
PDF_EXPORT_AZURE_IMAGE_ORIGINS=https://account.blob.core.windows.net
```

Use a comma-separated list for multiple accounts. Origins contain only the
scheme, hostname and optional port, with no SAS tokens. The default is empty:
Azure image downloads fail closed until configured. Do not derive the allowlist
from the storage-information response or allow all `*.blob.core.windows.net`.
An explicitly configured custom Azure HTTPS endpoint is supported.

EROS keeps its existing configuration. Internal DNS names, private IP addresses,
HTTP and nonstandard ports are supported only through the configured direct
EROS base or the configured Tools proxy. No private network, localhost or
metadata-service range is allowed implicitly. Do not add unrelated internal
services to these trusted settings. Configuration and DNS for allowed origins
must remain under operator control; the code does not pin resolved IP addresses.

## Audit traceability

The reported Tools API call is not evidence of a database-controlled arbitrary
origin. The subsequent image downloads needed an explicit origin policy and
redirect restriction, and project authorization occurred too late.

The issue describes two captures at `views.py:53` that appear to show the same
entry point. They are treated as one reported flow pending verification of the
Snyk finding identifiers; no count of two distinct findings is inferred.

Regression tests simulate all HTTP requests and cover authorized Azure, direct
and proxied EROS, and POP exports; forbidden URLs and ports; credential isolation
between providers; redirects; safe failure responses; and project access before
external calls. Validation results and the tested commit are recorded in the PR.

A new Snyk Code audit has not been run locally: no Snyk CLI or connected scanner
is available in this workspace. Before closing the audit acceptance criterion,
run Snyk Code against the PR commit, retain the report and full commit SHA, and
compare the finding identifiers from the September 30, 2026 captures. This
document does not claim that the scanner finding has disappeared.
