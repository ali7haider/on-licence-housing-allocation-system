"""Rank Rehabilitation Housing Units for a selected licensee."""

from collections.abc import Iterable

from models.attributes import (
    HardRequirementAttribute,
    MatchAttribute,
    TextAttribute,
    YesNoAttribute,
    ZoneAttribute,
)
from models.person import Licensee
from models.rhu import RHU


# Each tuple is: licensee value key, RHU value key, and the rule that compares them.
# The same ``matches`` call is used for every rule; the concrete rule class decides
# how its two values should be compared.
MATCHING_RULES: tuple[tuple[str, str, MatchAttribute], ...] = (
    # -- Hard requirements: a mismatch disqualifies the RHU in practice, so
    # it is scored far below any combination of soft-preference matches
    # while still being shown (sorted, not filtered — per the AO).
    ("category", "categories", HardRequirementAttribute("Category", 20)),
    ("gender", "accepted_genders", HardRequirementAttribute("Gender", 20)),

    # -- Conditions / restrictions
    ("night_curfew", "night_curfew", YesNoAttribute("Nighttime curfew", 10)),
    ("weekend_curfew", "weekend_curfew", YesNoAttribute("Weekend curfew", 10)),
    ("drug_searches_required", "drug_searches", YesNoAttribute("Drug searches", 10)),
    ("accessibility_required", "physical_accessibility", YesNoAttribute("Physical accessibility", 10)),
    ("is_young_offender", "young_offenders", YesNoAttribute("Young offender suitability", 10)),

    # -- Services / preferences
    ("medical_needs", "medical_services", TextAttribute("Medical services", 8)),
    ("transport_needs", "transport_links", TextAttribute("Transport links", 6)),
    ("disability_needs", "disability_support", TextAttribute("Disability support", 8)),
    ("mental_health_needs", "mental_health_support", TextAttribute("Mental health support", 8)),
    ("cultural_needs", "cultural_support", TextAttribute("Cultural or religious support", 6)),
    ("employment_needs", "employment_support", TextAttribute("Employment or training", 6)),
    ("family_access_needs", "family_access", TextAttribute("Family access", 5)),
    ("offending_triggers", "trigger_avoidance", TextAttribute("Offending trigger avoidance", 8)),
    ("licence_period", "allowed_licence_periods", TextAttribute("Licence period", 5)),

    # -- Location / safety
    ("exclusion_zones", "nearby_zones", ZoneAttribute("Exclusion zones", 50)),
    ("victim_exclusion_zones", "nearby_victim_zones", ZoneAttribute("Victim exclusion zones", 50)),
    ("school_exclusion_zones", "nearby_school_zones", ZoneAttribute("School exclusion zones", 50)),
    ("associate_exclusion_zones", "nearby_associate_zones", ZoneAttribute("Associate exclusion zones", 40)),
    ("specific_prisoner_exclusions", "specific_prisoner_exclusions",
     ZoneAttribute("Specific prisoner exclusions", 45)),
    ("prior_rhu_experience", "prior_rhu_experience", TextAttribute("Prior RHU experience", 4)),

    # -- Student Suggested 1: whether the RHU can support a licensee who is
    # on electronic/digital monitoring.
    ("digital_monitoring_required", "digital_monitoring_support",
     YesNoAttribute("Digital monitoring support (Student Suggested 1)", 8)),

    # -- Student Suggested 2: matches a licensee's need for a particular
    # peer environment (low conflict / structured / high support) to the
    # RHU's environment.
    ("peer_environment_need", "peer_environment",
     TextAttribute("Peer environment (Student Suggested 2)", 6)),

    ("future_expansion_1", "future_expansion_1", TextAttribute("Future Expansion 1", 3)),
    ("future_expansion_2", "future_expansion_2", TextAttribute("Future Expansion 2", 3)),
    ("future_expansion_3", "future_expansion_3", TextAttribute("Future Expansion 3", 3)),

    # -- Future Expansion 1-3: reserved for criteria the AO may add later.
    # Add a (licensee_key, rhu_key, MatchAttribute) tuple here — no other
    # code needs to change, since rank_rhus_for() iterates this tuple.
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

        ranked_rhus.append((rhu, score, warnings, rhu.cost_per_bed_per_day))

    return sorted(ranked_rhus, key=lambda result: result[1], reverse=True)
