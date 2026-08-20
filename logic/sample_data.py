"""Generate deterministic fictional data for development and demonstration."""

from datetime import date, timedelta
from random import Random

from models.enums import Category, Gender, LicenseeState
from models.person import Licensee
from models.rhu import RHU

FIRST_NAMES = [
    "Adam",
    "Aisha",
    "Callum",
    "Chloe",
    "Daniel",
    "Fatima",
    "Hassan",
    "Imogen",
    "Jack",
    "Jade",
    "Khalid",
    "Leah",
    "Marcus",
    "Nadia",
    "Owen",
    "Priya",
    "Ryan",
    "Sana",
    "Tariq",
    "Zara",
]
LAST_NAMES = [
    "Ahmed",
    "Ali",
    "Brown",
    "Campbell",
    "Davies",
    "Edwards",
    "Green",
    "Hughes",
    "Jones",
    "Khan",
    "Lewis",
    "Martin",
    "Murphy",
    "Patel",
    "Robinson",
    "Smith",
    "Taylor",
    "Walker",
    "White",
    "Wilson",
]
ZONE_TAGS = [
    "Durham City Centre",
    "Elm Street School",
    "Riverside Park",
    "North Road",
    "Market Place",
    "Station District",
    "University Quarter",
    "West End",
]
MEDICAL_SERVICES = ["GP", "Mental health clinic", "A&E", "Substance misuse service"]
BUS_ROUTES = ["6", "16", "20", "22", "34A", "X12"]


def generate_sample_data(
    licensee_count: int = 4_000,
    rhu_count: int = 15,
    seed: int = 42,
) -> tuple[list[Licensee], list[RHU]]:
    """Return fictional licensees and RHUs for local development.

    A seed makes the generated dataset repeatable, which is useful while the
    interface is being developed and tested.
    """
    random = Random(seed)
    rhus = _generate_rhus(random, rhu_count)
    licensees = _generate_licensees(random, licensee_count, rhus)
    return licensees, rhus


def _generate_rhus(random: Random, count: int) -> list[RHU]:
    """Create a small, varied collection of fictional hostels."""
    rhus: list[RHU] = []
    for number in range(1, count + 1):
        accepted_genders = random.choice(
            [[Gender.MALE.value], [Gender.FEMALE.value], [Gender.MIXED.value]]
        )
        rhus.append(
            RHU(
                name=f"Durham RHU {number}",
                address=f"{number * 10} Example Road, Durham, DH{number} 1AA",
                phone=f"0191 555 {number:04d}",
                email=f"rhu{number}@example.org",
                management_group=random.choice(
                    ["North East Support", "Safe Steps", "Community Homes"]
                ),
                contact_name=f"Manager {number}",
                cost_per_bed_per_day=round(random.uniform(55, 115), 2),
                capacity=random.randint(55, 85),
                emergency_capacity=random.randint(2, 8),
                short_term_beds=random.randint(3, 12),
                geographic_location=(
                    round(random.uniform(54.74, 54.81), 4),
                    round(random.uniform(-1.65, -1.52), 4),
                ),
                notes="Fictional development data.",
                attributes={
                    "categories": random.sample(
                        [category.value for category in Category],
                        k=random.randint(1, 3),
                    ),
                    "accepted_genders": accepted_genders,
                    "drug_searches": random.choice([True, False]),
                    "night_curfew": random.choice([True, False]),
                    "weekend_curfew": random.choice([True, False]),
                    "physical_accessibility": random.choice([True, False]),
                    "young_offenders": random.choice([True, False]),
                    "medical_services": random.sample(
                        MEDICAL_SERVICES, k=random.randint(1, 3)
                    ),
                    "transport_links": random.sample(
                        BUS_ROUTES, k=random.randint(1, 4)
                    ),
                    "nearby_zones": random.sample(ZONE_TAGS, k=random.randint(0, 2)),
                    "digital_monitoring_support": random.choice([True, False]),
                    "peer_environment": random.choice(
                        ["Low conflict", "Structured", "High support"]
                    ),
                },
            )
        )
    return rhus


def _generate_licensees(random: Random, count: int, rhus: list[RHU]) -> list[Licensee]:
    """Create fictional licensees and place allocated residents in RHUs."""
    licensees: list[Licensee] = []
    today = date.today()
    available_rhus = [rhu for rhu in rhus]

    for number in range(1, count + 1):
        state = random.choices(
            [LicenseeState.PENDING, LicenseeState.ALLOCATED, LicenseeState.EXITED],
            weights=[55, 20, 25],
            k=1,
        )[0]
        gender = random.choice([Gender.MALE, Gender.FEMALE])
        release_date = today + timedelta(days=random.randint(-120, 180))
        licence_end_date = release_date + timedelta(days=random.choice([90, 180, 365]))
        licensee = Licensee(
            name=f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
            home_address=f"{random.randint(1, 220)} Sample Street, County Durham",
            gender=gender,
            prison_role_id=f"PR-{number:05d}",
            release_date=release_date,
            licence_end_date=licence_end_date,
            current_location=random.choice(
                ["HMP Durham", "HMP Frankland", "HMP Low Newton"]
            ),
            category=random.choice(list(Category)),
            state=state,
            notes="Fictional development record.",
            attributes={
                "night_curfew": random.choice([True, False]),
                "weekend_curfew": random.choice([True, False]),
                "drug_searches_required": random.choice([True, False]),
                "medical_needs": random.sample(
                    MEDICAL_SERVICES, k=random.randint(0, 2)
                ),
                "transport_needs": random.sample(BUS_ROUTES, k=random.randint(0, 2)),
                "exclusion_zones": random.sample(ZONE_TAGS, k=random.randint(0, 2)),
                "digital_monitoring_required": random.choice([True, False]),
                "peer_environment_need": random.choice(
                    ["Low conflict", "Structured", "High support"]
                ),
            },
        )

        if state is LicenseeState.ALLOCATED:
            rhu = _choose_available_rhu(random, available_rhus, gender)
            if rhu is None:
                licensee.state = LicenseeState.PENDING
            else:
                licensee.current_rhu_name = rhu.name
                licensee.housing_exit_date = today + timedelta(
                    days=random.randint(7, 180)
                )
                rhu.resident_ids.append(licensee.prison_role_id)

        licensees.append(licensee)
    return licensees


def _choose_available_rhu(
    random: Random, rhus: list[RHU], gender: Gender
) -> RHU | None:
    """Choose an RHU with a free standard bed that accepts the licensee's gender."""
    choices = [
        rhu
        for rhu in rhus
        if len(rhu.resident_ids) < rhu.capacity
        and (
            gender.value in rhu.attributes["accepted_genders"]
            or Gender.MIXED.value in rhu.attributes["accepted_genders"]
        )
    ]
    return random.choice(choices) if choices else None
