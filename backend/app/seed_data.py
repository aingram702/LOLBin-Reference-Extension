"""
Seed script to bulk-load LOLBin/GTFOBins entries into the database.
Run: python -m app.seed_data
"""
import json
from pathlib import Path
from .database import SessionLocal, engine, Base
from .models import LolbinEntry

Base.metadata.create_all(bind=engine)

# Load from the same JSON used by the extension for consistency
DATA_PATH = Path(__file__).parent.parent.parent / "extension" / "data" / "lolbin_db.json"


def seed():
    db = SessionLocal()
    with open(DATA_PATH) as f:
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
