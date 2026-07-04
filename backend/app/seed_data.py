"""
Seed script to bulk-load LOLBin/GTFOBins entries into the database.
Run: python -m app.seed_data
"""
import json
import os
import sys
from pathlib import Path
from .database import SessionLocal, engine, Base
from .models import LolbinEntry

Base.metadata.create_all(bind=engine)

# Load from the same JSON used by the extension for consistency. The path can
# be overridden with LOLBIN_DB_PATH (e.g. inside the Docker image, where the
# repo layout differs from a local checkout).
_DEFAULT_PATHS = [
    Path(__file__).parent.parent.parent / "extension" / "data" / "lolbin_db.json",
    Path(__file__).parent / "data" / "lolbin_db.json",  # Docker: copied next to app/
]


def _resolve_data_path() -> Path:
    override = os.getenv("LOLBIN_DB_PATH")
    if override:
        return Path(override)
    for p in _DEFAULT_PATHS:
        if p.exists():
            return p
    return _DEFAULT_PATHS[0]


def seed():
    data_path = _resolve_data_path()
    if not data_path.exists():
        print(f"Seed data not found at {data_path}. "
              f"Set LOLBIN_DB_PATH to the lolbin_db.json location.", file=sys.stderr)
        sys.exit(1)

    db = SessionLocal()
    with open(data_path) as f:
        entries = json.load(f)

    for entry in entries:
        existing = db.query(LolbinEntry).filter(LolbinEntry.id == entry["id"]).first()
        if existing:
            continue
        db_entry = LolbinEntry(
            id=entry["id"],
            name=entry["name"],
            os=entry["os"],
            category=entry["category"],
            description=entry["description"],
            example_command=entry["example_command"],
            alt_commands=entry.get("alt_commands", []),
            detection_notes=entry.get("detection_notes"),
            references=entry.get("references", []),
        )
        db.add(db_entry)

    db.commit()
    print(f"Seeded {len(entries)} entries.")
    db.close()


if __name__ == "__main__":
    seed()
