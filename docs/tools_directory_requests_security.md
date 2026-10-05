# Tools API directory requests — issue #2039

## Qualification of the two Snyk findings

The findings concern `RunAdmin.save_model` calling `initialize_run_directory`
(creation) and `rename_run_directory` (old and new run labels). In both cases the
origin comes exclusively from the deployment-controlled
`EUPHROSYNE_TOOLS_API_URL`; user input is appended after `/data/`. An absolute
URL in a label cannot replace that origin. Arbitrary-host SSRF is therefore not
demonstrated by either concatenation alone.

The admin model's `valid_filename` validator already restricts labels to Unicode
word characters, hyphens and spaces; project slugs also have model validation.
This further restricts exploitation through the normal admin form. These checks
do not establish an HTTP boundary for hooks called directly, historical values
or future callers. Previously, separators, traversal and query/fragment
delimiters supplied to a hook could change the requested route. Requests could
also follow a redirect from the configured service to another destination.
Requests normally strips Authorization on a host change, but this does not
prevent the outbound request and is not an explicit origin policy (some
scheme/port changes retain authentication).

Creation and rename now use the same boundary: names are literal path segments,
and authenticated requests never follow redirects. The project directory hooks
use it too, since they share the same transport and routes.

## Contract with Tools API

The existing POST routes and empty request bodies remain unchanged:

- `/data/{project_slug}/init`
- `/data/{project_slug}/runs/{run_name}/init`
- `/data/{project_slug}/rename/{new_project_name}`
- `/data/{project_slug}/runs/{run_name}/rename/{new_run_name}`

Contract inspection: `api/data.py` and
`clients/azure/data.py::_generate_base_dir_path` in Tools API at commit
`b66a6fa5d8b8504cc541cc0e48ebe991b5c95f2e`. Its FastAPI routes use ordinary
single-segment string parameters; run names are passed unchanged to the data
client. No other repository needs modification for this contract.

Names are UTF-8 percent-encoded with no reserved URL characters left safe.
Spaces, Unicode, hyphens and underscores retain their exact value after one
server URL decoding pass. Literal `%` is encoded as `%25`: a name `%2f` is sent
as `%252f` and reaches Tools API as the literal name `%2f`, never as `/`. Input
is not pre-decoded, slugified or Unicode-normalized. Ordinary dots inside a name
are retained; complete `.` and `..` segments, empty names, raw `/` and `\`, and
ASCII control characters are rejected with `ValueError` before any request.
Encoding raw slashes would be insufficient because the ASGI server decodes
them before route matching. Query/fragment delimiters are encoded as data. The
admin's existing, stricter filename rules remain unchanged.

The configured base must be an absolute HTTP(S) URL without userinfo,
query, fragment, backslashes, whitespace or ASCII controls. A deployment prefix
and optional trailing slash are supported. This configuration, its DNS and its
network/proxy environment remain trusted: this is not a defense against a
deployment administrator deliberately configuring an unauthorized service.
Production should point directly to the intended HTTPS service endpoint.

Requests uses `allow_redirects=False`. Every 3xx response is treated as a failed
operation, including redirects within the configured origin and HTTP-to-HTTPS
upgrades. Creation and run rename log the failure, preserving their existing
best-effort behavior; project rename raises `RenameFailedError`, preserving its
caller contract. Redirect locations and authorization headers are not logged.

## Verification and remaining audit

The security tests use real Requests URL preparation and redirect handling with
an intercepted HTTP adapter and a dummy service token. They assert the exact
prepared destination, method, timeout and Authorization header, single decoding
of each name, rejection before sending invalid input, and absence of any second
request for 301/302/303/307/308 redirects, including another host, a
scheme-relative URL and a metadata address. No live Tools API or production
credentials are used.

A fresh Snyk Code scan must still be run on the corrected commit. Local behavior
tests are not a substitute for that scan. It was not run in this session: the
Snyk CLI is not installed and no connected Snyk tool is available to trigger an
authenticated audit. If the taint finding persists, review
its flow against the explicit segment validation/encoding and disabled redirect
policy above before deciding whether it is a false positive.
