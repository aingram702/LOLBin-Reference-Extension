# Notes for the Chrome Web Store reviewer

Paste the relevant parts of this into the dashboard's "Notes for reviewer"
field when submitting.

## What this extension does
LOLBin Reference Tool is a static, offline reference/lookup tool for
security professionals. It bundles a 142-entry JSON database describing
publicly-documented "Living-off-the-Land Binary" abuse techniques (mirroring
the public LOLBAS and GTFOBins project websites) and lets the user search it
from a popup. It does not execute any of the commands it displays, does not
interact with any remote system, and does not modify or read the content of
any web page.

## Why this is not a dual-use / security-risk violation
The extension is informational only, comparable to a searchable copy of
lolbas-project.github.io or gtfobins.github.io. It:
- Never executes, injects, or transmits any command shown in the UI.
- Has no `content_scripts`, no `activeTab`, no `scripting` permission, and no
  access to page content, tabs, or browsing history.
- Has no host permissions and makes zero network requests — everything
  renders from the bundled `data/lolbin_db.json`.

## Permissions used (minimal, both justified)
- `storage` — caches the bundled reference database in `chrome.storage.local`
  purely for instant popup load; never stores user input or browsing data.
- `clipboardWrite` — copies an example command to the clipboard only when the
  user directly clicks it.

No host permissions are requested.

## How to verify quickly
1. Load the unpacked `extension/` folder or the packaged `.zip`.
2. Click the toolbar icon — the popup loads a search box and 142 results
   with no network activity (check DevTools Network tab: no requests fire).
3. Type "certutil" — results filter client-side.
4. Click the Windows/Linux toggle — results filter by OS.
5. Click any command box — it copies to the clipboard and briefly shows a
   "Copied to clipboard!" confirmation.
6. Click a "Reference ↗" link — it opens the original LOLBAS/GTFOBins page
   in a new tab (the only outbound navigation the extension ever performs,
   and only on direct user click).

## Target audience / legal use
This tool is intended for authorized penetration testers, red teamers,
detection engineers, and security students. The description and this note
both state it is for authorized security testing and educational use only.
