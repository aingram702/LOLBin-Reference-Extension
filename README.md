# LOLBin Reference Tool

A Chrome Extension + backend API for quickly looking up Living-off-the-Land
Binaries (LOLBins), GTFOBins-style Linux binaries, and detection guidance
during authorized red team engagements.

⚠️ **For authorized security testing and educational purposes only.**
This tool is a *reference/lookup utility only* — it does not execute
commands, deploy payloads, or interact with remote systems. It functions
similarly to LOLBAS.github.io or GTFOBins.github.io, packaged as a
searchable browser extension with an optional team backend.

## Features
- 🔍 Instant search of Windows LOLBins and Linux GTFOBins-style binaries
- 📋 One-click copy of example commands
- 🛡️ Detection engineering notes per technique (Sigma-style guidance)
- 🔄 Fully offline: full database bundled locally, no network access at all
- 🖥️ PowerShell/Python CLI companions for terminal-based lookup

The published Chrome extension is offline-only by design — it requests no
host permissions and makes no network requests. A `backend/` FastAPI service
for a future team/Pro tier (live-updated DB, org notes, sync) lives in this
repo but is **not** wired into the extension build submitted to the Chrome
Web Store; see [SECURITY_AUDIT.md](SECURITY_AUDIT.md) for details.

The bundled database ships with **142 curated entries** (58 Windows LOLBAS +
84 Linux/Unix GTFOBins), each linking back to its authoritative source page.
It can be regenerated or extended — see [Regenerating the database](#regenerating-the-database).

## Repository Structure
- `extension/` — Chrome Extension (Manifest V3)
- `backend/` — FastAPI backend for Pro/Team tier (live updates, custom entries)
- `scripts/` — Standalone CLI tools (PowerShell + Python) using the same DB

## Quick Start

### Extension (Free/Offline Tier)
1. Go to `chrome://extensions`
2. Enable "Developer mode"
3. Click "Load unpacked" → select the `extension/` folder
4. Pin the extension and start searching

### Backend (Pro/Team Tier — optional)
The backend is optional — the extension is fully functional offline without it.
Run it from the **repository root** (the compose file injects `DATABASE_URL`
for the Postgres service automatically):

```bash
docker compose up --build
# API is served on http://localhost:8000  (docs at /docs)
```

Seed the database with the shared entries (inside the running container):

```bash
docker compose exec backend python -m app.seed_data
```

To run the backend directly (without Docker), copy the example env first:

```bash
cd backend
cp .env.example .env          # defaults to a local SQLite file
python -m app.seed_data
uvicorn app.main:app --reload
```

### CLI companions
Both CLIs read the same `extension/data/lolbin_db.json`:

```bash
# Python
python scripts/lolbin_lookup.py -n certutil
python scripts/lolbin_lookup.py --os linux --category "Privilege Escalation"
python scripts/lolbin_lookup.py --list-all

# PowerShell
./scripts/Get-LOLBinInfo.ps1 -Name certutil
./scripts/Get-LOLBinInfo.ps1 -Os windows -Category Execution
```

## Regenerating the database
`scripts/build_db.py` is the single source of truth for `lolbin_db.json`:

```bash
cd scripts
python build_db.py           # write the bundled curated dataset (offline, default)
python build_db.py --live    # fetch the COMPLETE upstream LOLBAS + GTFOBins
                             # catalogs and write the full mirror (needs network
                             # access to lolbas-project.github.io and github.com)
```

The curated dataset lives in `scripts/curated_entries.py`. The builder validates
the schema, rejects duplicate IDs and non-http references, and sorts entries
before writing.

## Security
See [SECURITY_AUDIT.md](SECURITY_AUDIT.md) for the full review. Highlights:
- The extension requests no host permissions and makes no network requests —
  the bundled `data/lolbin_db.json` is the only data source.
- The popup renders database content via HTML-escaping and only allows
  `http(s)` reference links, so a malicious `javascript:`/`data:` URL in the
  database can never become a clickable link.
- The backend (not part of the published extension) uses constant-time
  API-key comparison and validates all input.
- Secrets (`.env`) and local databases are git-ignored.

## Legal
For **authorized** security testing and educational use only. This is a
reference/lookup tool: it does not execute commands, deploy payloads, or
interact with remote systems. Use only against systems you own or are
explicitly authorized to test.
