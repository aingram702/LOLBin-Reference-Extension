import hmac
from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session
from .database import get_db
from .models import Organization


def verify_api_key(
    authorization: str = Header(...),
    db: Session = Depends(get_db)
) -> Organization:
    """
    Simple API key auth via Bearer token.
    Format: Authorization: Bearer <api_key>
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    # removeprefix (not replace) so a key that happens to contain "Bearer "
    # is not mangled.
    api_key = authorization[len("Bearer "):].strip()
    if not api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

    org = db.query(Organization).filter(Organization.api_key == api_key).first()
    # Constant-time confirmation to avoid leaking key validity via timing.
    # (The DB lookup itself is indexed; this guards the final comparison.)
    if not org or not hmac.compare_digest(org.api_key, api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")

    return org


def require_pro_tier(org: Organization = Depends(verify_api_key)) -> Organization:
    if org.tier not in ("pro", "team"):
        raise HTTPException(status_code=403, detail="This feature requires a Pro or Team subscription")
    return org
