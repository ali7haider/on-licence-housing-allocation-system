"""Rank Rehabilitation Housing Units for a selected licensee."""

from collections.abc import Iterable

from models.attributes import MatchAttribute, TextAttribute, YesNoAttribute, ZoneAttribute
from models.person import Licensee
from models.rhu import RHU


# Each tuple is: licensee value key, RHU value key, and the rule that compares them.
# The same ``matches`` call is used for every rule; the concrete rule class decides
# how its two values should be compared.
MATCHING_RULES: tuple[tuple[str, str, MatchAttribute], ...] = (
    ("category", "categories", TextAttribute("Category", 20, True)),
    ("gender", "accepted_genders", TextAttribute("Gender", 20, True)),
    ("night_curfew", "night_curfew", YesNoAttribute("Nighttime curfew", 10)),
    ("weekend_curfew", "weekend_curfew", YesNoAttribute("Weekend curfew", 10)),
    ("drug_searches_required", "drug_searches", YesNoAttribute("Drug searches", 10)),
    ("medical_needs", "medical_services", TextAttribute("Medical services", 8)),
    ("transport_needs", "transport_links", TextAttribute("Transport links", 6)),
    ("digital_monitoring_required", "digital_monitoring_support", YesNoAttribute("Digital monitoring", 8)),
    ("peer_environment_need", "peer_environment", TextAttribute("Peer environment", 6)),
    ("exclusion_zones", "nearby_zones", ZoneAttribute("Exclusion zones", 50)),
)


def rank_rhus_for(licensee: Licensee, rhus: Iterable[RHU]) -> list[tuple[RHU, int, list[str], float]]:
    """Rank every RHU for a licensee without filtering any options out.

    Each rule is evaluated polymorphically through ``MatchAttribute.matches``.
    Conflict outcomes become warnings so the allocation officer can make the
    final judgement with the full ranked list visible.
    """
    ranked_rhus: list[tuple[RHU, int, list[str], float]] = []
    licensee_values = {
        "category": licensee.category.value,
        "gender": licensee.gender.value,
        **licensee.attributes,
    }

    for rhu in rhus:
        score = 0
        warnings: list[str] = []
        for licensee_key, rhu_key, attribute in MATCHING_RULES:
            rhu_value = rhu.attributes.get(rhu_key)
            # An RHU marked as mixed accepts both recorded licensee genders.
            if rhu_key == "accepted_genders" and rhu_value:
                accepted_genders = (
                    [value.strip() for value in rhu_value.split(",")]
                    if isinstance(rhu_value, str)
                    else list(rhu_value)
                )
                if any(str(value).casefold() == "mixed" for value in accepted_genders):
                    rhu_value = [*accepted_genders, licensee_values["gender"]]
            outcome = attribute.matches(
                licensee_values.get(licensee_key),
                rhu_value,
            )
            score += outcome.score
            if outcome.is_conflict:
                warnings.append(outcome.reason)

        if len(rhu.resident_ids) >= rhu.capacity:
            score -= 100
            warnings.append("RHU has no standard beds available")

        ranked_rhus.append((rhu, score, warnings, rhu.cost_per_bed_per_day))

    return sorted(ranked_rhus, key=lambda result: result[1], reverse=True)
