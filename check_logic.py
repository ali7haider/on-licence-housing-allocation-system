"""Terminal-only check for sample data generation and RHU ranking."""

from random import choice

from logic.matching import rank_rhus_for
from logic.sample_data import generate_sample_data


def main() -> None:
    """Generate test data and print the five best RHU options for one person."""
    licensees, rhus = generate_sample_data()
    licensee = choice(licensees)
    ranked_rhus = rank_rhus_for(licensee, rhus)

    print(f"Generated {len(licensees)} licensees and {len(rhus)} RHUs.")
    print(f"\nLicensee: {licensee.name} ({licensee.prison_role_id})")
    print("Top 5 RHU options:")
    for position, (rhu, score, warnings, cost) in enumerate(ranked_rhus[:5], start=1):
        warning_text = "; ".join(warnings) if warnings else "No conflict warnings"
        print(f"{position}. {rhu.name} | score: {score} | cost/day: £{cost:.2f}")
        print(f"   {warning_text}")


if __name__ == "__main__":
    main()
