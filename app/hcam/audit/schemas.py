from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AuditEventRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_id: str
    actor_id: str | None
    action: str = Field(min_length=1)
    target_type: str = Field(min_length=1)
    target_id: str | None
    occurred_at: datetime
    source: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    outcome: str = Field(min_length=1)
    context: dict[str, Any]
