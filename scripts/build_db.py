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
# GTFOBins markdown parsing
#
# Each _gtfobins/<name>.md file is Jekyll markdown with a YAML frontmatter
# block whose `functions:` key maps a technique name (shell, sudo, suid,
# file-read, ...) to a list of items, each with a `code` (and optional
# `description`). We parse that frontmatter into (functions, descriptions).
# PyYAML is used when available; a dependency-free fallback parser handles
# environments without it so `--live` never silently produces empty entries.
# ---------------------------------------------------------------------------

def _extract_frontmatter(raw):
    raw = raw.lstrip("﻿")  # tolerate a UTF-8 BOM
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", raw, re.S)
    return m.group(1) if m else ""


def _parse_functions_manual(fm):
    """Parse the GTFOBins `functions:` block without external dependencies.

    Returns (functions, descriptions) where functions is an ordered list of
    (technique_name, [code_string, ...]).
    """
    lines = fm.splitlines()
    n = len(lines)
    i = 0
    while i < n and not re.match(r"^functions:\s*$", lines[i]):
        i += 1
    i += 1  # step past 'functions:'

    functions, index, descriptions = [], {}, []

    def bucket(name):
        if name not in index:
            index[name] = []
            functions.append((name, index[name]))
        return index[name]

    cur = None
    while i < n:
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        indent = len(line) - len(line.lstrip(" "))
        if indent == 0:  # dedented out of the functions block
            break

        m_fn = re.match(r"^ {2}([A-Za-z0-9][\w./ -]*):\s*$", line)
        if m_fn:
            cur = bucket(m_fn.group(1))
            i += 1
            continue

        m_code = re.match(r"^\s*-?\s*code:\s*(.*)$", line)
        if m_code is not None and cur is not None:
            val = m_code.group(1).strip()
            if val in ("|", "|-", "|+", ">", ">-", ">+", ""):  # block scalar
                base, i = indent, i + 1
                block = []
                while i < n:
                    bl = lines[i]
                    if not bl.strip():
                        block.append("")
                        i += 1
                        continue
                    if (len(bl) - len(bl.lstrip(" "))) <= base:
                        break
                    block.append(bl)
                    i += 1
                nonempty = [b for b in block if b.strip()]
                if nonempty:
                    pad = min(len(b) - len(b.lstrip(" ")) for b in nonempty)
                    code = "\n".join(b[pad:] if b.strip() else "" for b in block).strip()
                    if code:
                        cur.append(code)
                continue
            cur.append(val)
            i += 1
            continue

        m_desc = re.match(r"^\s*-?\s*description:\s*(.*)$", line)
        if m_desc and m_desc.group(1).strip() not in ("", "|", ">"):
            descriptions.append(m_desc.group(1).strip())
        i += 1

    return functions, descriptions


def parse_gtfobins(raw):
    """Return (functions, descriptions) from a GTFOBins markdown file."""
    fm = _extract_frontmatter(raw)
    if not fm:
        return [], []
    try:
        import yaml
        meta = yaml.safe_load(fm) or {}
        funcs = meta.get("functions") or {}
        out, descriptions = [], []
        for name, items in funcs.items():
            codes = []
            for it in (items or []):
                if isinstance(it, dict):
                    if it.get("code"):
                        codes.append(str(it["code"]).strip())
                    if it.get("description"):
                        descriptions.append(str(it["description"]).strip())
                elif isinstance(it, str) and it.strip():
                    codes.append(it.strip())
            out.append((str(name), codes))
        return out, descriptions
    except Exception:
        # PyYAML missing or the frontmatter tripped it — fall back.
        return _parse_functions_manual(fm)


def _pretty_cat(name):
    return name.replace("-", " ").replace("_", " ").strip().title()


def _is_gtfobins_page(raw):
    """True if a markdown file is a GTFOBins binary page (has a functions block).

    We identify binary pages by content rather than by directory name, so the
    build is resilient to the upstream repo's layout (the collection directory
    name has moved/varied between checkouts).
    """
    fm = _extract_frontmatter(raw)
    return bool(fm) and re.search(r"^functions\s*:", fm, re.M) is not None


def _gtfobins_sources(get):
    """Yield (slug, raw_markdown) for every GTFOBins binary page.

    The GitHub *contents* API proved unreliable in some environments (returning
    an empty list -> zero Linux entries), so this prefers a shallow ``git
    clone`` and falls back to the Git *trees* API. Binary pages are located by
    their ``functions:`` frontmatter, not by a hardcoded directory name.
    """
    import glob
    import os
    import subprocess
    import tempfile

    repo_url = "https://github.com/GTFOBins/GTFOBins.github.io.git"

    # --- Strategy 1: shallow clone (preferred) ------------------------------
    try:
        with tempfile.TemporaryDirectory() as td:
            print("Cloning GTFOBins repository (shallow) ...")
            subprocess.run(
                ["git", "clone", "--depth", "1", "--quiet", repo_url, td],
                check=True, capture_output=True, text=True, timeout=600)
            md_files = sorted(glob.glob(os.path.join(td, "**", "*.md"), recursive=True))
            kept = 0
            for f in md_files:
                raw = Path(f).read_text(encoding="utf-8", errors="replace")
                if _is_gtfobins_page(raw):
                    kept += 1
                    yield os.path.basename(f)[:-3], raw
            print(f"  cloned {len(md_files)} .md files, {kept} are GTFOBins pages")
            if kept:
                return
            sample = [os.path.relpath(p, td) for p in md_files[:8]]
            print(f"  no GTFOBins pages found in clone; sample paths: {sample}")
            print("  trying the GitHub API ...")
    except FileNotFoundError:
        print("  git not found on PATH; falling back to the GitHub API ...")
    except subprocess.CalledProcessError as e:
        detail = (e.stderr or "").strip().splitlines()[-1:] or [str(e)]
        print(f"  git clone failed ({detail[0][:120]}); falling back to the GitHub API ...")
    except Exception as e:  # pragma: no cover - defensive
        print(f"  clone error ({e}); falling back to the GitHub API ...")

    # --- Strategy 2: Git trees API (recursive) ------------------------------
    api = "https://api.github.com/repos/GTFOBins/GTFOBins.github.io"
    meta = json.loads(get(api))
    branch = meta.get("default_branch", "master") if isinstance(meta, dict) else "master"
    tree = json.loads(get(f"{api}/git/trees/{branch}?recursive=1"))
    if not isinstance(tree, dict) or "tree" not in tree:
        msg = tree.get("message") if isinstance(tree, dict) else str(tree)[:120]
        raise RuntimeError(
            f"Could not list GTFOBins files via the GitHub API ({msg!r}). "
            f"Install git (preferred) or set GITHUB_TOKEN and retry.")
    md_paths = [t["path"] for t in tree["tree"]
                if t.get("type") == "blob" and t["path"].endswith(".md")]
    print(f"  {len(md_paths)} .md files in tree; scanning for GTFOBins pages ...")
    raw_base = f"https://raw.githubusercontent.com/GTFOBins/GTFOBins.github.io/{branch}"
    kept = 0
    for p in md_paths:
        raw = get(f"{raw_base}/{p}").decode("utf-8", "replace")
        if _is_gtfobins_page(raw):
            kept += 1
            yield os.path.basename(p)[:-3], raw
    print(f"  {kept} GTFOBins pages via API")


# ---------------------------------------------------------------------------
# Live mode: build the complete mirror from upstream sources
# ---------------------------------------------------------------------------

def build_live():
    """Fetch and transform the full LOLBAS + GTFOBins datasets.

    Kept dependency-light: uses urllib for LOLBAS' JSON API and a shallow
    ``git clone`` (falling back to the GitHub trees API) for GTFOBins markdown.
    Run this on a machine with network access to regenerate the full database.
    """
    import os
    import urllib.request

    token = os.getenv("GITHUB_TOKEN")

    def get(url):
        headers = {"User-Agent": "lolbin-build/1.0"}
        if token and "api.github.com" in url:
            headers["Authorization"] = f"Bearer {token}"
        req = urllib.request.Request(url, headers=headers)
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
    def make_gtfo_entry(slug, raw):
        functions, descriptions = parse_gtfobins(raw)
        cmds = [code for _, codes in functions for code in codes]
        cat_names = [name for name, _ in functions]

        uniq_cats = list(dict.fromkeys(_pretty_cat(c) for c in cat_names))
        category = " / ".join(uniq_cats[:4]) if uniq_cats else "Shell / Privilege Escalation"
        techniques = ", ".join(uniq_cats[:6]) or "shell access / privilege escalation"
        description = descriptions[0] if descriptions else (
            f"GTFOBins: '{slug}' can be abused for {techniques.lower()}. "
            f"Exact abuse depends on the SUID bit, sudo rights, or capabilities "
            f"granted to it — see the reference for each context.")

        return {
            "id": uid(slug, "nix"),
            "name": slug,
            "os": "linux",
            "category": category,
            "description": description,
            "example_command": cmds[0] if cmds else f"# See {gtfo(slug)}",
            "alt_commands": cmds[1:8],
            "detection_notes": "Audit SUID/SGID bits, sudo rules, and file "
                               "capabilities on this binary; alert on it spawning a "
                               "shell or reading/writing sensitive files outside its "
                               "normal role.",
            "references": [gtfo(slug)],
        }

    gtfo_count = 0
    for slug, raw in _gtfobins_sources(get):
        entries.append(make_gtfo_entry(slug, raw))
        gtfo_count += 1

    print(f"  built {gtfo_count} GTFOBins (linux) entries")
    if gtfo_count == 0:
        raise RuntimeError("No GTFOBins entries were built — check network/git access.")
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
