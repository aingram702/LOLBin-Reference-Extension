# Security Audit & Code Review — LOLBin Reference Tool

Scope: Chrome extension (`extension/`), FastAPI backend (`backend/`), CLI
scripts (`scripts/`), and deployment config. This document records the findings
from a full code review, debugging pass, and security audit, and the
remediations applied.

> Threat-model note: the extension is a **local reference/lookup tool**. It does
> not execute the commands it displays. The primary trust boundary is the
> optional **Pro-sync backend**, whose responses are merged into the local
> database and then rendered in the popup — i.e. remotely-sourced, potentially
> attacker-controlled content is rendered in a privileged extension context.

---

## Findings

### C1 — (CRITICAL, functional) `popup.js` had a syntax error → popup completely broken
`escapeAttr` contained `return String(str).replace(/"/g, """);` — three literal
double-quote characters, an unterminated string literal. `node --check` and any
browser would fail to parse `popup.js`, so **the entire popup rendered blank for
every user**. The intended code was `.replace(/"/g, "&quot;")`.
**Fix:** rewrote `escapeAttr` with a correct, fuller entity map (`& " ' < >`).
**Status:** Fixed. Verified with `node --check` and unit tests.

### H1 — (HIGH, XSS) Reference URLs rendered as `href` with no scheme validation
`renderResults` built `<a href="${escapeAttr(r)}">` directly from each entry's
`references`. Attribute-escaping does **not** neutralize dangerous URL schemes,
so a Pro-sync (or tampered local) entry with `references: ["javascript:…"]` (or
`data:`/`vbscript:`) produced a clickable link that executes script in the
extension origin when clicked.
**Fix:** added `safeUrl()`, which parses each URL and drops anything whose
protocol is not `http:`/`https:`; unsafe references are filtered out before
rendering. Also added `rel="noopener noreferrer"` to defeat reverse tabnabbing.
**Status:** Fixed. Verified `javascript:`, `data:`, `vbscript:`, `file:` are all
blocked while `http(s)` pass.

### H2 — (HIGH, auth) `.replace("Bearer ", "")` mangled valid API keys
`auth.verify_api_key` stripped the scheme with `str.replace`, which removes
**every** occurrence of `"Bearer "`. A legitimate key containing that substring
was silently corrupted, causing valid keys to be rejected (and altering the
lookup value).
**Fix:** slice off exactly the `"Bearer "` prefix once; reject empty keys.
**Status:** Fixed. Unit-tested against a key containing `"Bearer "`.

### M1 — (MEDIUM, timing) Non-constant-time API-key comparison
Final key validation relied solely on the DB equality lookup. Added an explicit
`hmac.compare_digest(org.api_key, api_key)` check to avoid leaking key validity
through comparison timing.
**Status:** Fixed. See also *Residual risks* re: plaintext key storage.

### M2 — (MEDIUM, DoS/robustness) `delete_custom_entry` could 500 on bad input
`entry_id` (a path string) was compared directly against a UUID column. A
non-UUID value (e.g. `foo`, or an injection probe) caused the driver to raise,
returning a 500 and leaking a stack trace instead of a clean 404.
**Fix:** validate `uuid.UUID(entry_id)` up front and return 404 on failure.
**Status:** Fixed. Unit-tested with non-UUID and SQL-ish inputs.

### M3 — (MEDIUM, availability) Popup depended on `onInstalled` having run
The DB was only seeded into `chrome.storage.local` by the background
`onInstalled` handler. MV3 service workers are ephemeral and `onInstalled` does
not fire on every browser start, so a cleared storage area left the popup
permanently empty with no recovery path.
**Fix:** (a) popup now self-heals via `loadDatabase()`, falling back to fetching
the bundled `data/lolbin_db.json` and re-caching it; (b) background adds an
`onStartup` re-seed when storage is empty; (c) both paths validate the payload
is an array.
**Status:** Fixed.

### M4 — (MEDIUM, deploy) Backend never connected to Postgres; missing env file
`docker-compose.yml` defined a Postgres service but set **no** `DATABASE_URL` on
the backend, so it silently defaulted to an in-container SQLite file (data lost
on rebuild, Postgres unused). It also referenced `./backend/.env`, which does
not exist, and the README told users to `cp .env.example .env` — but no
`.env.example` was committed.
**Fix:** inject `DATABASE_URL` (Postgres) via compose `environment`; add a
service healthcheck + `depends_on: condition: service_healthy`; commit
`backend/.env.example`; fix the Dockerfile build context so the seed data is
bundled; correct the README quick-start.
**Status:** Fixed.

### L1 — (LOW, robustness) Unvalidated remote merge & sync response handling
`background.mergeEntries` trusted every synced object to have an `id`, and
`popup.handleSync` dereferenced `response.success` without checking for
`chrome.runtime.lastError`/undefined responses.
**Fix:** skip synced entries without a string `id`; guard the sync callback
against missing responses and surface the runtime error message.
**Status:** Fixed.

### L2 — (LOW, hygiene) No `.gitignore`
Secrets (`.env`) and local SQLite DBs risked being committed.
**Fix:** added `.gitignore` covering `.env`, `*.db`/`*.sqlite*`, `__pycache__`,
virtualenvs, and editor/OS cruft.
**Status:** Fixed.

---

## Verification
- `node --check` passes on `background.js` and `popup.js`.
- Node harness: `safeUrl` blocks `javascript:`/`data:`/`vbscript:`/`file:` and
  allows `http(s)`; `escapeAttr` escapes quotes/angle brackets; search/filter
  returns correct results across all 142 entries; every shipped reference URL is
  `http(s)`.
- Python harness: Bearer parsing preserves keys containing `"Bearer "` and
  rejects empty/mis-schemed headers; UUID validation rejects non-UUID input.
- `build_db.py` schema validator enforces required fields, unique IDs, valid OS
  values, and http-only references.

> The FastAPI app could not be booted live in the audit sandbox (PyPI egress is
> blocked, so FastAPI/SQLAlchemy could not be installed). Backend logic changes
> were verified in isolation as described above; a live integration run is
> recommended in an environment with package access.

---

## Residual risks / recommendations (not code-fixed here)
1. **Plaintext API keys.** `Organization.api_key` is stored and compared in
   clear. Recommend storing a hash (e.g. SHA-256 of a high-entropy key) and
   comparing hashes; the constant-time check (M1) is a stopgap.
2. **No rate limiting / lockout** on the auth endpoints. Add per-IP throttling
   to slow key brute-forcing.
3. **`host_permissions` placeholder.** `manifest.json` and `background.js` point
   at `https://api.yourdomain.com`. Set a real, pinned host before publishing;
   avoid wildcards.
4. **HTTPS/cert pinning for sync.** Ensure the Pro backend is HTTPS-only; even
   with the scheme fixes above, treat all synced fields as untrusted.
5. **CSP.** The MV3 default CSP (no inline script) is relied upon — keep
   `popup.html` free of inline handlers/scripts (currently compliant).

---

## Update — Chrome Web Store submission build (2026-07-07)
Residual risks #3 and #4 above are resolved for the *published extension* by
removing the Pro-sync feature from this build entirely: `host_permissions`,
`background.js`'s `syncWithBackend`/`mergeEntries`, and the popup's "Sync Pro"
button/handler were deleted. `https://api.yourdomain.com` was always a
placeholder with no real backend deployed, so the shipped extension now
requests only `storage` and `clipboardWrite` — no host permissions, no network
egress, no untrusted remote data path into the popup. The findings above
(H2, M1, M4, L1, and residual risks #1/#2/#4) remain accurate for the
`backend/` FastAPI service and apply if/when a Pro-sync tier is reintroduced
as a separate, explicitly-permissioned build.
