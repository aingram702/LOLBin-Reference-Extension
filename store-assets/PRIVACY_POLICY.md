# Privacy Policy — LOLBin Reference Tool

**Last updated: 2026-07-07**

LOLBin Reference Tool ("the extension") is a browser extension that provides
an offline, searchable reference of Living-off-the-Land Binaries (Windows
LOLBAS and Linux GTFOBins-style techniques) for authorized security testing
and detection-engineering purposes.

## Summary

**The extension collects no data, transmits no data, and communicates with no
server.** It has no host permissions and makes no network requests of any
kind.

## What the extension stores

The extension bundles a static JSON database (`data/lolbin_db.json`,
142 entries) inside the installed package. On first run, this database is
copied into `chrome.storage.local` — Chrome's local, on-device storage area —
purely so the popup can render instantly without re-reading the packaged file
every time it opens.

That cached copy contains only the extension's own reference data (binary
names, categories, example commands, detection notes, and public source
links). It never contains anything you type, browse, or copy — search
queries are matched in memory while the popup is open and are never written
to storage, logged, or sent anywhere.

## What the extension does *not* do

- It does not request access to your browsing history, tabs, or the content
  of any web page.
- It does not collect personally identifiable information, authentication
  credentials, financial information, health information, or location data.
- It does not use analytics, telemetry, or crash-reporting services.
- It does not make network requests — there are no host permissions in the
  manifest, and the extension has no remote server to talk to.
- It does not share, sell, or transfer any data to third parties, because it
  does not collect any data in the first place.

## Clipboard access

The extension requests the `clipboardWrite` permission solely so that
clicking an example command in the popup can copy that text to your
clipboard as a convenience. This only happens in direct response to a click
you make; the extension never reads the clipboard and never writes to it
automatically.

## Reference links

Each entry may include one or more links back to its original source
(lolbas-project.github.io or gtfobins.github.io). These links only open when
you click them, in a new browser tab, using your browser's normal navigation
— the extension itself does not fetch or track anything about those pages.

## Changes to this policy

If a future version of this extension adds functionality that changes what
data is collected or transmitted (for example, an optional team-sync backend
offered as a separate, explicitly-permissioned feature), this policy will be
updated first and the Chrome Web Store listing will reflect the change before
it ships.

## Contact

Questions about this policy or the extension's data practices can be filed
as an issue on the project's GitHub repository.
