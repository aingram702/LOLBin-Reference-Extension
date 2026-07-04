from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class LolbinEntryOut(BaseModel):
    id: str
    name: str
    os: str
    category: str
    description: str
    example_command: str
    alt_commands: List[str] = []
    detection_notes: Optional[str] = None
    references: List[str] = []

    class Config:
        from_attributes = True


class CustomEntryIn(BaseModel):
    name: str
    os: str
    category: str
    description: str
    example_command: str
    detection_notes: Optional[str] = None


class CustomEntryOut(CustomEntryIn):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True
