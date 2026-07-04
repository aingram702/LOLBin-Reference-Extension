from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
from typing import List
import uuid

from .database import get_db, engine, Base
from .models import LolbinEntry, CustomEntry, Organization
from .schemas import LolbinEntryOut, CustomEntryIn, CustomEntryOut
from .auth import verify_api_key, require_pro_tier

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="LOLBin Reference Tool API",
    description="Backend for Pro/Team tier live-updated LOLBin database and org-private entries.",
    version="1.0.0"
)


@app.get("/")
def root():
    return {"status": "ok", "service": "lolbin-reference-tool-api"}


@app.get("/v1/lolbin", response_model=List[LolbinEntryOut])
def list_all_entries(db: Session = Depends(get_db), org: Organization = Depends(verify_api_key)):
    return db.query(LolbinEntry).all()


@app.get("/v1/lolbin/updates", response_model=dict)
def get_updates_since(
    since: str,
    db: Session = Depends(get_db),
    org: Organization = Depends(require_pro_tier)
):
    """Pro tier: returns entries updated after a given ISO timestamp."""
    try:
        since_dt = datetime.fromisoformat(since)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid 'since' timestamp format")

    entries = db.query(LolbinEntry).filter(LolbinEntry.updated_at > since_dt).all()
    return {
        "entries": [LolbinEntryOut.model_validate(e).model_dump() for e in entries],
        "count": len(entries)
    }


@app.post("/v1/lolbin/custom", response_model=CustomEntryOut)
def add_custom_entry(
    entry: CustomEntryIn,
    db: Session = Depends(get_db),
    org: Organization = Depends(require_pro_tier)
):
    """Pro/Team tier: add a private, org-scoped LOLBin-style entry."""
    db_entry = CustomEntry(
        id=uuid.uuid4(),
        org_id=org.id,
        **entry.model_dump()
    )
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)

    return CustomEntryOut(
        id=str(db_entry.id),
        created_at=db_entry.created_at,
        **entry.model_dump()
    )


@app.get("/v1/lolbin/custom", response_model=List[CustomEntryOut])
def list_custom_entries(
    db: Session = Depends(get_db),
    org: Organization = Depends(require_pro_tier)
):
    """Pro/Team tier: list all org-private entries."""
    entries = db.query(CustomEntry).filter(CustomEntry.org_id == org.id).all()
    return [
        CustomEntryOut(
            id=str(e.id),
            name=e.name,
            os=e.os,
            category=e.category,
            description=e.description,
            example_command=e.example_command,
            detection_notes=e.detection_notes,
            created_at=e.created_at
        ) for e in entries
    ]


@app.delete("/v1/lolbin/custom/{entry_id}")
def delete_custom_entry(
    entry_id: str,
    db: Session = Depends(get_db),
    org: Organization = Depends(require_pro_tier)
):
    # Validate the UUID up front so a malformed id yields a clean 404 rather
    # than a 500 from the database driver rejecting the cast.
    try:
        entry_uuid = uuid.UUID(entry_id)
    except (ValueError, AttributeError, TypeError):
        raise HTTPException(status_code=404, detail="Entry not found")

    entry = db.query(CustomEntry).filter(
        and_(CustomEntry.id == entry_uuid, CustomEntry.org_id == org.id)
    ).first()

    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    db.delete(entry)
    db.commit()
    return {"status": "deleted"}
