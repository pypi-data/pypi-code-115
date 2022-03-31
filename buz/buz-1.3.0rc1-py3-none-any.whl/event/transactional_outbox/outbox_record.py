from datetime import datetime
from typing import Dict, Optional

from dataclasses import dataclass


@dataclass(frozen=True)
class OutboxRecord:
    event_id: str
    event_fqn: str
    event_payload: Dict
    created_at: datetime
    delivered_at: Optional[datetime] = None
    delivery_errors: int = 0
