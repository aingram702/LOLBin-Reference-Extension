#!/usr/bin/env python3
"""
build_db.py — Generator for the LOLBin Reference Tool database.

Two modes:

  python build_db.py            # (default) write the bundled curated database
                                # from the CURATED dataset below. Works fully
                                # offline. This is what ships in the extension.

  python build_db.py --live     # fetch the COMPLETE upstream datasets from the
                                # official LOLBAS JSON API and the GTFOBins
                                # markdown source, transform them into this
                                # tool's schema, and write the full mirror.
                                # Requires outbound network access to:
                                #   https://lolbas-project.github.io/api/lolbas.json
                                #   https://github.com/GTFOBins/GTFOBins.github.io
                                # (git clone or the GitHub contents API)

Output is written to extension/data/lolbin_db.json — the single source of truth
shared by the Chrome extension, the FastAPI backend seeder, and the CLI tools.

Schema (per entry):
  id, name, os, category, description, example_command,
  alt_commands[], detection_notes, references[]
"""

import argparse
import json
import re
import sys
from pathlib import Path

OUT_PATH = Path(__file__).parent.parent / "extension" / "data" / "lolbin_db.json"

LOLBAS_REF = "https://lolbas-project.github.io/lolbas/{kind}/{name}/"
GTFO_REF = "https://gtfobins.github.io/gtfobins/{name}/"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def lol(name_slug, kind="Binaries"):
    return LOLBAS_REF.format(kind=kind, name=name_slug)


def gtfo(name_slug):
    return GTFO_REF.format(name=name_slug)


def validate(entries):
    """Fail loudly on schema / integrity problems before writing."""
    required = {"id", "name", "os", "category", "description", "example_command"}
    seen = set()
    errors = []
    for i, e in enumerate(entries):
        missing = required - e.keys()
        if missing:
            errors.append(f"[{i}] {e.get('id', '?')}: missing {sorted(missing)}")
        if e.get("os") not in ("windows", "linux", "macos"):
            errors.append(f"[{i}] {e.get('id', '?')}: bad os {e.get('os')!r}")
        if e.get("id") in seen:
            errors.append(f"[{i}] duplicate id {e.get('id')!r}")
        seen.add(e.get("id"))
        for r in e.get("references", []):
            if not (r.startswith("http://") or r.startswith("https://")):
                errors.append(f"[{i}] {e.get('id')}: non-http reference {r!r}")
    if errors:
        print("VALIDATION FAILED:", file=sys.stderr)
        print("\n".join(errors), file=sys.stderr)
        sys.exit(1)
    return entries


def write(entries):
    entries = validate(entries)
    entries.sort(key=lambda e: (e["os"], e["id"]))
    OUT_PATH.write_text(json.dumps(entries, indent=2, ensure_ascii=False) + "\n")
    win = sum(1 for e in entries if e["os"] == "windows")
    lin = sum(1 for e in entries if e["os"] == "linux")
    mac = sum(1 for e in entries if e["os"] == "macos")
    print(f"Wrote {len(entries)} entries -> {OUT_PATH}")
    print(f"  windows={win}  linux={lin}  macos={mac}")


# ---------------------------------------------------------------------------
# Live mode: build the complete mirror from upstream sources
# ---------------------------------------------------------------------------

def build_live():
    """Fetch and transform the full LOLBAS + GTFOBins datasets.

    Kept dependency-light: uses urllib for LOLBAS' JSON API and the GitHub
    contents API for GTFOBins markdown. Run this on a machine with network
    access to regenerate the complete database.
    """
    import urllib.request

    def get(url):
        req = urllib.request.Request(url, headers={"User-Agent": "lolbin-build/1.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.read()

    seen_ids = set()

    def uid(base, *hints):
        """Return a unique id, disambiguating collisions with the given hints.

        LOLBAS ships several binaries that share a filename stem across kinds
        (e.g. SyncAppvPublishingServer.exe vs .vbs), and a few names overlap
        between Windows and Linux (ftp, curl). Deriving the id from the stem
        alone therefore collides; this appends a hint (file extension or 'nix')
        and finally a numeric suffix to guarantee uniqueness.
        """
        base = base.lower()
        candidates = [base] + [f"{base}-{h}" for h in hints if h]
        for cand in candidates:
            if cand not in seen_ids:
                seen_ids.add(cand)
                return cand
        n = 2
        while f"{base}-{n}" in seen_ids:
            n += 1
        seen_ids.add(f"{base}-{n}")
        return f"{base}-{n}"

    def http_only(urls):
        return [u for u in urls if isinstance(u, str)
                and (u.startswith("http://") or u.startswith("https://"))]

    entries = []

    # ---- LOLBAS (Windows) --------------------------------------------------
    print("Fetching LOLBAS JSON API ...")
    lolbas = json.loads(get("https://lolbas-project.github.io/api/lolbas.json"))
    for b in lolbas:
        name = b.get("Name", "")
        slug = Path(name).stem  # certutil.exe -> certutil
        ext = Path(name).suffix.lstrip(".").lower()  # exe / vbs / dll
        commands = b.get("Commands") or []
        cmds = [c.get("Command", "").strip() for c in commands if c.get("Command")]
        cats = sorted({c.get("Category", "") for c in commands if c.get("Category")})
        descs = [c.get("Description", "") for c in commands if c.get("Description")]
        detects = []
        for d in b.get("Detection") or []:
            detects.extend(str(v) for v in d.values() if v)
        refs = [b["url"]] if b.get("url") else []
        for r in b.get("Resources") or []:
            if r.get("Link"):
                refs.append(r["Link"])
        if not cmds:
            continue
        entries.append({
            "id": uid(slug, ext),
            "name": name,
            "os": "windows",
            "category": " / ".join(cats) or "Execution",
            "description": (descs[0] if descs else "") or f"LOLBAS entry for {name}.",
            "example_command": cmds[0],
            "alt_commands": cmds[1:],
            "detection_notes": " ".join(detects[:4]) or None,
            "references": http_only(refs)[:6],
        })

    # ---- GTFOBins (Linux) --------------------------------------------------
    print("Fetching GTFOBins index ...")
    listing = json.loads(get(
        "https://api.github.com/repos/GTFOBins/GTFOBins.github.io/contents/_gtfobins"))
    for item in listing:
        if not item["name"].endswith(".md"):
            continue
        slug = item["name"][:-3]
        raw = get(item["download_url"]).decode("utf-8", "replace")
        # frontmatter: functions -> {FunctionName: [{code, description}]}
        funcs = re.findall(r"^functions:\s*$", raw, re.M)
        code_blocks = re.findall(r"code:\s*\|?\s*\n((?:\s{6,}.*\n?)+)", raw)
        cats = re.findall(r"^\s{2}(\w[\w -]*):\s*$", raw, re.M)
        cmds = [re.sub(r"^\s+", "", cb).strip() for cb in code_blocks if cb.strip()]
        if not cmds:
            cmds = [f"# See {gtfo(slug)}"]
        entries.append({
            "id": uid(slug, "nix"),
            "name": slug,
            "os": "linux",
            "category": " / ".join(sorted(set(cats))[:3]) or "Shell / Privilege Escalation",
            "description": f"GTFOBins entry: abusable Unix binary '{slug}'. "
                           f"See reference for exact SUID/sudo/capabilities context.",
            "example_command": cmds[0],
            "alt_commands": cmds[1:5],
            "detection_notes": "Audit SUID/sudo permissions and capabilities on this "
                               "binary; alert on it spawning shells or reading/writing "
                               "sensitive files outside its normal role.",
            "references": [gtfo(slug)],
        })

    return entries


# ---------------------------------------------------------------------------
# Curated dataset (offline default) is imported from a sibling module so this
# file stays focused on transformation/IO logic.
# ---------------------------------------------------------------------------

def build_curated():
    from curated_entries import CURATED
    return CURATED


def main():
    ap = argparse.ArgumentParser(description="Build the LOLBin Reference database.")
    ap.add_argument("--live", action="store_true",
                    help="Fetch the complete mirror from upstream LOLBAS/GTFOBins.")
    args = ap.parse_args()

    entries = build_live() if args.live else build_curated()
    write(entries)


if __name__ == "__main__":
    main()
