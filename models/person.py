"""Person and licensee data models."""

from dataclasses import dataclass, field
from datetime import date

from models.enums import Category, Gender, LicenseeState
from models.history import LicenceBreach


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
    breaches: list[LicenceBreach] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Convert valid string values into the model's enum types."""
        if not isinstance(self.gender, Gender):
            self.gender = Gender(self.gender)
        if not isinstance(self.category, Category):
            self.category = Category(self.category)
        if not isinstance(self.state, LicenseeState):
            self.state = LicenseeState(self.state)
