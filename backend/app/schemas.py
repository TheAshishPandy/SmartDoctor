"""Public response schemas; do not expose internal authorization metadata."""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class PatientRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    display_label: str
    created_at: datetime
