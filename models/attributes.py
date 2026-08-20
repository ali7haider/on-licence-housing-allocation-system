"""Lightweight storage for named matching attribute values."""

from dataclasses import dataclass


@dataclass
class AttributeValue:
    """A named value attached to either a licensee or an RHU."""

    name: str
    value: object
