# Chrome Web Store Listing — LOLBin Reference Tool

Copy-paste source for the Developer Dashboard listing fields. Character counts
are noted where the Store enforces a limit.

---

## Extension name
(max 45 characters — current: 21)

```
LOLBin Reference Tool
```

## Summary / short description
(max 132 characters — current: 114)

```
Instant offline lookup for Windows LOLBins & Linux GTFOBins-style binaries during authorized red team engagements.
```

## Category
Primary: **Developer Tools**
(Alternative if unavailable in your region's taxonomy: **Productivity**)

## Language
English (United States)

---

## Detailed description
(max 16,000 characters — shown in full on the listing page, first ~300 shown
before "Read more")

```
LOLBin Reference is a fast, fully offline lookup tool for Living-off-the-Land
Binaries (LOLBins) — the built-in OS binaries that can be abused to execute
code, download payloads, escalate privileges, or bypass defenses using
functionality Microsoft, Apple, and Linux distributions ship on every machine.
It works the same way as LOLBAS.github.io and GTFOBins.github.io, but packaged
as a searchable browser popup so red teamers, pentesters, and detection
engineers don't have to leave the browser tab they're already in.

⚠️ FOR AUTHORIZED SECURITY TESTING AND EDUCATIONAL USE ONLY. This is a
reference/lookup tool — it does not execute commands, deploy payloads, or
connect to any remote system. It only displays information about techniques,
exactly like the public LOLBAS and GTFOBins project sites.

WHAT'S INSIDE
• 142 curated entries — 58 Windows LOLBAS binaries + 84 Linux/Unix
  GTFOBins-style binaries — each linking back to its authoritative source
  (lolbas-project.github.io or gtfobins.github.io).
• Example commands for each technique, with one-click copy to clipboard.
• Sigma-style detection engineering notes on almost every entry, so blue
  teams and detection engineers can turn a technique lookup directly into an
  alerting rule.
• Instant client-side search across binary name, category, technique, and
  description — no page reloads, no loading spinners.
• Windows / Linux / All filter toggle to narrow results to one platform.

WHY IT'S OFFLINE-ONLY
The entire database ships inside the extension package. There are no host
permissions, no network requests, and no telemetry — everything renders from
the bundled, git-versioned dataset. Reference links open the original
LOLBAS/GTFOBins pages in a new tab only when you click them.

WHO IT'S FOR
• Red teamers and penetration testers who need a fast, authoritative
  technique reference during an authorized engagement.
• Detection engineers writing Sigma rules or SIEM alerts for LOLBin abuse.
• Students and blue teamers learning how native OS tooling gets abused, and
  how to detect it.

HOW TO USE IT
Click the extension icon, type a binary name (e.g. "certutil"), a technique
category (e.g. "privilege escalation"), or a keyword from the description.
Use the Windows/Linux toggle to narrow the platform. Click any example
command to copy it to your clipboard.

RESPONSIBLE USE
Use only against systems you own or are explicitly authorized to test. This
extension is a reference utility, not an exploitation tool — it never sends,
receives, or executes anything on your behalf.

Source available and open to review: see the project repository linked below.
```

---

## Single purpose description
(Required field — one sentence describing the extension's single purpose)

```
Look up and search a bundled, offline reference database of Living-off-the-Land
Binaries (Windows LOLBAS / Linux GTFOBins-style techniques) and copy example
commands, for authorized security testing and detection-engineering reference.
```

## Permission justifications
(Required per-permission in the "Privacy practices" tab)

**`storage`**
```
Used to cache the bundled 142-entry LOLBin database in chrome.storage.local
so the popup opens instantly on repeat use without re-reading the packaged
JSON file every time. Stores only the extension's own bundled reference data
— no user-entered or browsing data is ever written to storage.
```

**`clipboardWrite`**
```
Used only when the user clicks an example command inside the popup, to copy
that command text to the clipboard as a convenience. No clipboard read
access is requested, and nothing is copied without a direct user click.
```

**Host permissions**: none requested. The extension makes no network
requests and has no remote data source — the popup only renders the bundled
`data/lolbin_db.json`.

## Data usage disclosure
(Required checkboxes in the "Privacy practices" tab — answer "No" to all of
the following, since the extension collects nothing and transmits nothing)

- Personally identifiable information — **Not collected**
- Health information — **Not collected**
- Financial and payment information — **Not collected**
- Authentication information — **Not collected**
- Personal communications — **Not collected**
- Location — **Not collected**
- Web history — **Not collected**
- User activity — **Not collected**
- Website content — **Not collected**

Certify: *"I do not sell or transfer user data to third parties, outside of
the approved use cases"* / *"I do not use or transfer user data for purposes
unrelated to the item's single purpose"* / *"I do not use or transfer user
data to determine creditworthiness or for lending purposes"* — all **true**,
since no user data is collected at all.

## Privacy policy URL
Point this at `PRIVACY_POLICY.md` once hosted (e.g. via GitHub Pages or the
repo's raw file URL — see note in that file). Required because the listing
requests any permission at all, even though no data is actually collected.

---

## Store assets checklist
| Asset | Spec | File |
|---|---|---|
| Icon | 128×128 PNG | `extension/icons/icon128.png` (already in package) |
| Small promo tile | 440×280 PNG | `store-assets/images/small_tile_440x280.png` |
| Marquee promo tile (optional, for featuring) | 1400×560 PNG | `store-assets/images/marquee_tile_1400x560.png` |
| Screenshots (1–5, 1280×800 or 640×400) | PNG/JPEG | `store-assets/images/screenshot_1_search.png`, `screenshot_2_linux_filter.png`, `screenshot_3_detection.png`, `screenshot_4_offline.png` |

## Support / contact
Add a support URL or email in the dashboard (required field). Suggest the
GitHub repository's Issues page if no dedicated support email exists yet.
