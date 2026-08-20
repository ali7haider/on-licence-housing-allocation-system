"""Rehabilitation Housing Unit data model."""

from dataclasses import dataclass, field
from datetime import date


@dataclass
class RHU:
    """A hostel or other Rehabilitation Housing Unit."""

    name: str
    address: str
    phone: str
    email: str
    management_group: str
    contact_name: str
    cost_per_bed_per_day: float
    capacity: int
    emergency_capacity: int
    short_term_beds: int
    geographic_location: tuple[float, float]
    notes: str = ""
    attributes: dict[str, object] = field(default_factory=dict)
    resident_ids: list[str] = field(default_factory=list)
    total_owed: float = 0.0
    last_payment_date: date = field(default_factory=date.today)
    
