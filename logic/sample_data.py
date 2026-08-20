"""Generate deterministic fictional data for development and demonstration."""

from datetime import date, timedelta
from random import Random

from models.enums import Category, Gender, LicenseeState
from models.person import Licensee
from models.rhu import RHU

FIRST_NAMES = [
    "James", "William", "Charles", "George", "Thomas", "Henry", "Edward",
    "John", "Robert", "Richard", "David", "Michael", "Peter", "Paul",
    "Mary", "Elizabeth", "Margaret", "Anne", "Catherine", "Jane", "Sarah",
    "Emily", "Emma", "Charlotte", "Sophie", "Olivia", "Amelia", "Jessica",
    "Hamish", "Fraser", "Dougal", "Alistair", "Iain", "Euan", "Angus",
    "Isla", "Fiona", "Morag", "Elspeth", "Catriona", "Eilidh", "Ailsa",
    "Dafydd", "Gareth", "Rhys", "Owain", "Hywel", "Ieuan", "Geraint",
    "Ceri", "Sian", "Ffion", "Gwen", "Bethan", "Carys", "Eleri",
    "Declan", "Niall", "Rory", "Ciaran", "Aidan", "Brendan", "Eamon",
    "Ciara", "Maeve", "Orla", "Niamh", "Aoife", "Roisin", "Siobhan",
    "Mohammed", "Zara", "Aisha", "Priya", "Rahul", "Amina", "Sadia",
    "Kofi", "Adeola", "Taiwo", "Maya", "Rani", "Sofia", "Ismail",
    "Wayne", "Darren", "Craig", "Dean", "Lee", "Gary", "Barry", "Steve",
    "Tracy", "Donna", "Michelle", "Sharon", "Karen", "Angela", "Paula",
]

LAST_NAMES = [
    "Smith", "Jones", "Taylor", "Brown", "Williams", "Wilson", "Johnson",
    "Davies", "Robinson", "Wright", "Thompson", "Evans", "Walker", "White",
    "Roberts", "Green", "Hall", "Wood", "Jackson", "Clarke", "Harrison",
    "Martin", "Thompson", "Morgan", "Cooper", "Anderson", "Hill", "Price",
    "Baker", "Cox", "Miller", "Parker", "Collins", "Edwards", "Morris",
    "Campbell", "MacDonald", "Robertson", "Stewart", "Murray", "McDonald",
    "McKenzie", "MacKenzie", "Fraser", "Kennedy", "MacLeod", "Cameron",
    "Davies", "Evans", "Thomas", "Jones", "Williams", "Lewis", "Morgan",
    "Roberts", "Hughes", "Edwards", "Griffiths", "Price", "Rees",
    "O'Brien", "O'Connor", "Ryan", "Murray", "Kelly", "Kennedy", "Walsh",
    "McGuire", "McIntyre", "Armstrong", "Graham", "Adams", "McDonald",
    "Harrington", "Westminster", "Huntingdon", "Sheffield", "Chesterfield",
    "Dunmore", "Hamilton", "Sutherland", "Richmond", "Windsor",
    "Thatcher", "Higgins", "Pritchard", "Pickering", "Whitehead", "Blackwell",
    "Underwood", "Goodwin", "Oakley", "Bentley", "Clayton", "Sawyer",
]

ZONE_TAGS = [
    "Durham City Centre", "Elm Street School", "Riverside Park", "North Road",
    "Market Place", "Station District", "University Quarter", "West End",
    "Cathedral Quarter", "Old Elvet", "Wharton Park", "Gilesgate",
    "South Street", "New Inn", "Dragonville", "Aykley Heads",
    "Shopping District", "Industrial Estate", "Residential Zone", "Business Park",
    "Leisure Complex", "Community Centre", "Hospital Area", "College Campus",
    "High Street", "Promenade", "Castle View", "Town Hall Square",
]

MEDICAL_SERVICES = [
    "GP", "Mental health clinic", "A&E", "Substance misuse service",
    "Dental surgery", "Eye clinic", "Counselling service", "Podiatry",
    "Physiotherapy", "Community pharmacy", "District nursing",
    "Eating disorder support", "Prison healthcare", "Sexual health clinic",
    "Pain management", "Dementia support", "Stroke rehabilitation",
]

BUS_ROUTES = [
    "6", "16", "20", "22", "34A", "X12",
    "1", "2", "4", "7", "8", "10", "11", "12", "14", "15", "18",
    "21", "23", "24", "25", "27", "28", "29", "30", "35", "36",
    "40", "42", "43", "45", "50", "55", "60", "62", "64", "66",
    "X1", "X2", "X5", "X10", "X15", "X20", "X21", "X46",
    "RAPID 1", "RAPID 2", "EXPRESS", "LINK", "CONNECTOR",
]

MANAGEMENT_GROUPS = [
    "North East Support", "Safe Steps", "Community Homes",
    "Durham Housing Alliance", "Northumbria Care", "Tyne Valley Housing",
    "Wear Valley Support", "Teesside Foundation", "County Durham Homes",
    "Cleveland Community Trust", "North East Housing Group",
    "Home North East", "Durham Wellbeing Centre", "The Riverside Group",
    "Twelve Housing", "First Steps Housing", "Foundations NE",
]

PRISON_NAMES = [
    "HMP Durham", "HMP Frankland", "HMP Low Newton",
    "HMP Holme House", "HMP Kirklevington", "HMP Northumberland",
    "HMP Deerbolt", "HMP Acklington", "HMP Wealstun",
    "HMP Wandsworth", "HMP Belmarsh", "HMP Pentonville",
    "HMP Brixton", "HMP Wormwood Scrubs", "HMP Leeds",
    "HMP Hull", "HMP Wakefield", "HMP Nottingham",
]


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
    used_names: set[str] = set()
    
    places = ["Durham", "Chester-le-Street", "Consett", "Stanley", "Spennymoor", 
              "Newton Aycliffe", "Bishop Auckland", "Darlington", "Stockton", 
              "Middlesbrough", "Sunderland", "Newcastle", "Gateshead", 
              "Washington", "South Shields"]
    
    for number in range(1, count + 1):
        place = random.choice(places)
        name = f"{place} RHU {random.choice(['Lodge', 'House', 'Centre', 'Residence', 'Place'])}"
        while name in used_names:
            name = f"{place} RHU {random.choice(['Lodge', 'House', 'Centre', 'Residence', 'Place'])} {number}"
        used_names.add(name)
        accepted_genders = random.choice(
            [[Gender.MALE.value], [Gender.FEMALE.value], [Gender.MIXED.value]]
        )
        rhus.append(
            RHU(
                name=name,
                address=f"{number * 10} {random.choice(['Main', 'Station', 'Church', 'Market', 'North', 'South', 'East', 'West'])} Road, {place}, DH{number} 1AA",
                phone=f"0191 {random.randint(200, 999)} {random.randint(1000, 9999)}",
                email=f"rhu{number}@example.org",
                management_group=random.choice(MANAGEMENT_GROUPS),
                contact_name=f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
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
                    "nearby_zones": random.sample(ZONE_TAGS, k=random.randint(0, 3)),
                    "digital_monitoring_support": random.choice([True, False]),
                    "peer_environment": random.choice(
                        ["Low conflict", "Structured", "High support", "Mixed"]
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
        # Generate more realistic age distributions
        state = random.choices(
            [LicenseeState.PENDING, LicenseeState.ALLOCATED, LicenseeState.EXITED],
            weights=[55, 20, 25],
            k=1,
        )[0]
        gender = random.choice([Gender.MALE, Gender.FEMALE])
        
        # Realistic release date distribution (more likely to be recent)
        release_date = today + timedelta(days=random.randint(-180, 90))
        licence_end_date = release_date + timedelta(days=random.choice([90, 180, 365]))
        
        # Create licensee with weighted attributes for more realistic data
        licensee = Licensee(
            name=f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
            home_address=f"{random.randint(1, 220)} {random.choice(['Main', 'Station', 'Church', 'Park', 'North', 'South', 'East', 'West'])} Street, County Durham",
            gender=gender,
            prison_role_id=f"PR-{number:05d}",
            release_date=release_date,
            licence_end_date=licence_end_date,
            current_location=random.choice(PRISON_NAMES),
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
                    ["Low conflict", "Structured", "High support", "Mixed"]
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