"""History records used for operational audit and licence-condition tracking."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class AuditEvent:
    """A timestamped status or housing-placement change."""

    timestamp: datetime
    prison_role_id: str
    action: str
    from_state: str | None = None
    to_state: str | None = None
    from_rhu: str | None = None
    to_rhu: str | None = None
    details: str = ""


@dataclass(frozen=True)
class LicenceBreach:
    """A recorded breach of a licensee's licence conditions."""

    recorded_at: datetime
    details: str
