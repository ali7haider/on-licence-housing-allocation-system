"""Enumerations used by the housing allocation data models."""

from enum import Enum


class LicenseeState(str, Enum):
    """The three groups shown in the allocation officer's workflow."""

    PENDING = "Pending"
    ALLOCATED = "Allocated"
    EXITED = "Exited"


class Gender(str, Enum):
    """Gender recorded for a licensee or accepted by an RHU."""

    MALE = "Male"
    FEMALE = "Female"
    MIXED = "Mixed"


class Category(str, Enum):
    """Simple risk/support categories used by the pilot data."""

    A = "A"
    B = "B"
    C = "C"
