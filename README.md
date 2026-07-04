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
- 🔄 Offline-first: full database bundled locally, works without internet
- ☁️ Optional Pro backend: live-updated DB, private org notes, team sync
- 🖥️ PowerShell/Python CLI companions for terminal-based lookup

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
```bash
cd backend
cp .env.example .env
docker compose up --build
