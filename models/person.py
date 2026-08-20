"""Person and licensee data models."""

from dataclasses import dataclass, field
from datetime import date

from models.enums import Category, Gender, LicenseeState


@dataclass
class Person:
    """Common identifying data for a person."""

    name: str
    home_address: str
    gender: Gender


@dataclass
class Licensee(Person):
    """A person supervised on licence and awaiting or using housing."""

    prison_role_id: str
    release_date: date
    licence_end_date: date
    current_location: str
    category: Category
    state: LicenseeState = LicenseeState.PENDING
    notes: str = ""
    attributes: dict[str, object] = field(default_factory=dict)
    current_rhu_name: str | None = None
    housing_exit_date: date | None = None
    shortlist: list[str] = field(default_factory=list)
