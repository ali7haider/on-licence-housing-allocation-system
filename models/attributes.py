"""Matching attribute classes used to compare licensees and RHUs."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable


@dataclass
class MatchOutcome:
    """The explanation produced when one matching rule is evaluated."""

    score: int
    reason: str
    is_conflict: bool = False


class MatchAttribute(ABC):
    """Base class for one type of licencee-to-RHU matching rule."""

    def __init__(self, label: str, weight: int) -> None:
        self.label = label
        self.weight = weight

    @abstractmethod
    def matches(self, licensee_value: object, rhu_value: object) -> MatchOutcome:
        """Compare values and return an explainable match outcome."""


class YesNoAttribute(MatchAttribute):
    """Match a requirement that an RHU either provides or does not provide."""

    def matches(self, licensee_value: object, rhu_value: object) -> MatchOutcome:
        if not bool(licensee_value):
            return MatchOutcome(0, f"{self.label}: not required")
        if bool(rhu_value):
            return MatchOutcome(self.weight, f"{self.label}: provided")
        return MatchOutcome(-self.weight, f"{self.label}: not provided", True)


class TextAttribute(MatchAttribute):
    """Match a value or list of values, such as routes or services."""

    def __init__(self, label: str, weight: int, conflict_on_mismatch: bool = False) -> None:
        super().__init__(label, weight)
        self.conflict_on_mismatch = conflict_on_mismatch

    def matches(self, licensee_value: object, rhu_value: object) -> MatchOutcome:
        wanted = _normalise_values(licensee_value)
        available = _normalise_values(rhu_value)
        if not wanted:
            return MatchOutcome(0, f"{self.label}: no requirement recorded")

        shared_values = wanted & available
        if shared_values:
            display_values = ", ".join(sorted(shared_values))
            return MatchOutcome(self.weight, f"{self.label}: matches {display_values}")

        return MatchOutcome(
            -self.weight,
            f"{self.label}: no matching provision",
            self.conflict_on_mismatch,
        )


class ZoneAttribute(MatchAttribute):
    """Flag overlaps between a licensee exclusion-zone tag and an RHU zone tag."""

    def matches(self, licensee_value: object, rhu_value: object) -> MatchOutcome:
        excluded_zones = _normalise_values(licensee_value)
        nearby_zones = _normalise_values(rhu_value)
        overlapping_zones = excluded_zones & nearby_zones
        if overlapping_zones:
            display_zones = ", ".join(sorted(overlapping_zones))
            return MatchOutcome(
                -self.weight,
                f"{self.label}: RHU is near excluded zone(s): {display_zones}",
                True,
            )
        if excluded_zones:
            return MatchOutcome(self.weight, f"{self.label}: no zone conflict")
        return MatchOutcome(0, f"{self.label}: no exclusion zone recorded")


@dataclass
class AttributeValue:
    """A named value attached to either a licensee or an RHU."""

    name: str
    value: object


def _normalise_values(value: object) -> set[str]:
    """Convert a scalar or iterable value into a comparable set of text values."""
    if value is None:
        return set()
    if isinstance(value, str):
        return {value.casefold()}
    if isinstance(value, Iterable):
        return {str(item).casefold() for item in value}
    return {str(value).casefold()}
